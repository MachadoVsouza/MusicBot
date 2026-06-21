import re
import json
from .repository import ChatRepository
from app.langchain.repository import OllamaRepository
from app.rag.service import RagService
from app.rag.sintese import RagSintese
from app.agents.service import run_agent, run_agent_stream
from app.chat.memory import get_chat_history, get_history_messages

SYSTEM_PROMPT = """Voce eh o MusicBot, um assistente musical inteligente e entusiasta.

## Identidade
- Voce eh um especialista em musica: teoria, historia, generos, artistas, albuns, cultura musical
- Responda SEMPRE em portugues brasileiro, com linguagem natural e calorosa
- Demonstre paixao genuina por musica, mas mantenha o profissionalismo

## Estilo de Resposta
- **Seja completo**: desenvolva o raciocinio com comeco, meio e fim — nunca corte uma resposta no meio
- **Contextualize**: ao falar de um artista/musica/album, inclua curiosidades, influencias, contexto historico mas sem tornar a resposta longa demais
- **Seja honesto**: se nao souber algo com certeza, diga "Nao tenho certeza, mas..." e diferencie claramente fato de opiniao
- **Estruture bem**: use paragrafos curtos. Para listas (ex: discografia), use bullets com "•"
- **Emojis**: use no MAXIMO 2 por resposta, apenas para destacar itens musicais (🎵 album, 🎸 artista, 🎧 playlist). Nunca use emojis aleatorios

## Limites
- Mantenha-se estritamente no tema musica. Se o usuario perguntar de outro assunto, responda educadamente que voce eh especializado em musica e redirecione a conversa

## Formato
- Respostas diretas: 2-4 paragrafos + fontes se souber
- Listas (ex: top 5, discografia): titulo + bullets
- Prefira Markdown leve para legibilidade (negrito para nomes de artistas/albuns, bullets para listas)
"""

SYSTEM_PROMPT_RAG = """Voce eh o MusicBot, um assistente musical especializado que esta consultando uma base de conhecimento verificada.

## Instrucao Principal
Use o contexto delimitado por <contexto> abaixo como fonte PRIMARIA da sua resposta. Se o contexto e seu conhecimento geral se complementarem, voce pode integra-los, mas sempre **priorize e cite** o que veio do contexto.

## Regras
- Responda SEMPRE em portugues brasileiro
- Seja detalhado e completo com base no que esta no contexto
- **SEMPRE cite qual documento/fonte esta usando** (ex: "Segundo o artigo X...", "De acordo com o documento Y...")
- Se o contexto cobrir parcialmente a pergunta: responda com o que tem e mencione claramente o que ficou de fora
- Se o contexto nao tiver informacao relevante: diga "A base de conhecimento nao contem informacoes suficientes sobre isso, mas posso complementar com meu conhecimento geral" e entao responda
- Nunca corte a resposta no meio — sempre conclua o raciocinio

<contexto>
{contexto}
</contexto>

## Estilo
- Paragrafos bem estruturados
- Diferencie claramente: o que veio do contexto (fatos) vs o que voce esta inferindo (opiniao)
"""

INTENT_PATTERNS = re.compile(
    r"\b(toca|tocar|busca|buscar|procura|procurar|encontra|encontrar|ouvir|ouça|play|pesquisa|minhas|meus|favoritos|recentes|curtidas|curti|playlists|cria|adiciona|artista)\b",
    re.IGNORECASE
)


def _detectar_intencao_spotify(mensagem: str) -> bool:
    return bool(INTENT_PATTERNS.search(mensagem))


class ChatService:
    def __init__(self):
        self.chat_repo = ChatRepository()
        self.llm_repo  = OllamaRepository()
        self.rag_svc   = RagService()
        self.rag_sintese = RagSintese()

    def iniciar_chat(self, spotify_id: str, titulo: str = "Nova conversa") -> dict:
        self.chat_repo.get_or_create_usuario(spotify_id)
        chat = self.chat_repo.criar_chat(spotify_id, titulo)
        return {"chat_id": chat.id, "titulo": chat.titulo}

    def listar_chats(self, spotify_id: str) -> list[dict]:
        chats = self.chat_repo.listar_chats(spotify_id)
        return [
            {
                "id":         c.id,
                "titulo":     c.titulo,
                "status":     c.status.value,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in chats
        ]

    def enviar_mensagem(self, spotify_id: str, chat_id: int, mensagem: str, token: str = None) -> dict | None:
        chat = self.chat_repo.get_chat(chat_id, spotify_id)
        if not chat:
            return None

        historico  = self.chat_repo.get_historico(chat_id)
        pergunta   = self.chat_repo.salvar_pergunta(chat_id, mensagem)
        historico.append({"role": "user", "content": mensagem})

        midia      = None
        usou_rag   = False
        usou_agent = False
        fragmentos = []

        if token and _detectar_intencao_spotify(mensagem):
            resultado_agent   = run_agent(token, mensagem, historico)
            conteudo_resposta = resultado_agent["resposta"]
            midia             = resultado_agent.get("midia")
            usou_agent        = True
        else:
            # Usa RAG com síntese — respeita o provider do usuário
            resultado_sintese = self.rag_sintese.consultar(mensagem, limite=3, spotify_id=spotify_id)
            usou_rag = resultado_sintese["usou_rag"]
            fragmentos = resultado_sintese["fragmentos"]

            if usou_rag and resultado_sintese["resposta"]:
                conteudo_resposta = resultado_sintese["resposta"]
            else:
                system_prompt = SYSTEM_PROMPT
                conteudo_resposta = self.llm_repo.gerar_resposta(
                    historico     = historico,
                    system_prompt = system_prompt,
                    spotify_id    = spotify_id,
                )

        if not conteudo_resposta:
            conteudo_resposta = "Desculpe, não consegui processar sua mensagem. Tente novamente."

        resposta = self.chat_repo.salvar_resposta(pergunta.id, conteudo_resposta, usou_rag)

        if usou_rag and fragmentos and resposta:
            self.rag_svc.salvar_fontes(resposta.id, [f["fragmento_id"] for f in fragmentos])

        return {
            "chat_id":     chat_id,
            "pergunta_id": pergunta.id,
            "resposta_id": resposta.id,
            "pergunta":    mensagem,
            "resposta":    conteudo_resposta,
            "usou_rag":    usou_rag,
            "usou_agent":  usou_agent,
            "midia":       midia,
            "fontes":      fragmentos if usou_rag else [],
        }

    def stream_mensagem(self, spotify_id: str, chat_id: int, mensagem: str, token: str = None) -> dict | None:
        """
        Versão streaming — retorna um gerador de chunks + metadados finais.
        O blueprint consome o gerador via SSE.
        """
        chat = self.chat_repo.get_chat(chat_id, spotify_id)
        if not chat:
            return None

        historico  = self.chat_repo.get_historico(chat_id)
        pergunta   = self.chat_repo.salvar_pergunta(chat_id, mensagem)
        historico.append({"role": "user", "content": mensagem})

        midia      = None
        usou_rag   = False
        fragmentos = []

        # Agent com streaming real
        if token and _detectar_intencao_spotify(mensagem):
            # Objeto mutável compartilhado entre generator e after_stream
            state = type("State", (), {"midia": None, "chunks": [], "tool_calls": []})()

            def _stream_agent():
                for event in run_agent_stream(token, mensagem, historico):
                    if event["type"] == "token":
                        state.chunks.append(event["content"])
                        yield event["content"]
                    elif event["type"] == "tool_call":
                        state.tool_calls.append(event)
                    elif event["type"] == "midia":
                        state.midia = event["midia"]
                    elif event["type"] == "error":
                        state.chunks.append(event["content"])
                        yield event["content"]

            stream_gen = _stream_agent()

            def _after_stream_agent():
                conteudo = "".join(state.chunks)
                if not conteudo:
                    conteudo = "Desculpe, não consegui processar sua mensagem."
                resposta = self.chat_repo.salvar_resposta(pergunta.id, conteudo, False)
                # Retorna midia junto com a resposta — o blueprint precisa disso
                return resposta, state.midia

            return {
                "stream":       stream_gen,
                "after_stream": _after_stream_agent,
                "pergunta_id":  pergunta.id,
                "resposta_id":  None,
                "usou_rag":     False,
                "midia":        None,  # será preenchido pelo after_stream
                "tool_calls":   None,  # será preenchido pelo after_stream
            }

        # RAG — respeita o provider do usuário
        fragmentos = self.rag_svc.buscar_contexto(mensagem, limite=3)
        usou_rag   = len(fragmentos) > 0

        if usou_rag:
            contexto      = "\n\n---\n\n".join(f["conteudo"][:300] for f in fragmentos)
            system_prompt = SYSTEM_PROMPT_RAG.format(contexto=contexto)
        else:
            system_prompt = SYSTEM_PROMPT

        chunks_gerados = []

        def _stream_e_acumula():
            for chunk in self.llm_repo.gerar_stream(historico, system_prompt, spotify_id=spotify_id):
                chunks_gerados.append(chunk)
                yield chunk

        stream_gen = _stream_e_acumula()

        # Salva resposta após o stream terminar — feito no blueprint após consumir o gerador
        def _after_stream():
            conteudo = "".join(chunks_gerados)
            if not conteudo:
                conteudo = "Desculpe, não consegui processar sua mensagem."
            resposta = self.chat_repo.salvar_resposta(pergunta.id, conteudo, usou_rag)
            if usou_rag and fragmentos and resposta:
                self.rag_svc.salvar_fontes(resposta.id, [f["fragmento_id"] for f in fragmentos])
            return resposta

        return {
            "stream":       stream_gen,
            "after_stream": _after_stream,
            "pergunta_id":  pergunta.id,
            "resposta_id":  None,
            "usou_rag":     usou_rag,
            "midia":        midia,
            "fragmentos":   fragmentos,
        }

    def get_mensagens(self, spotify_id: str, chat_id: int) -> list[dict] | None:
        chat = self.chat_repo.get_chat(chat_id, spotify_id)
        if not chat:
            return None
        mensagens = self.chat_repo.get_mensagens_completas(chat_id)
        return [
            {
                "id":          f"{m['role']}-{i}",
                "role":        "user" if m["role"] == "user" else "bot",
                "content":     m["content"],
                "timestamp":   m["timestamp"],
                "resposta_id": m.get("resposta_id"),
                "pergunta_id": m.get("pergunta_id"),
                "usou_rag":    m.get("usou_rag"),
            }
            for i, m in enumerate(mensagens)
        ]
