import re
from .repository import ChatRepository
from app.langchain.repository import OllamaRepository
from app.rag.service import RagService
from app.agents.service import run_agent

SYSTEM_PROMPT = """Você é o MusicBot, um assistente musical inteligente e apaixonado por música.

Diretrizes:
- Use emojis apenas para diferenciar bandas,musicas,playlist etc, mas não exagere — o foco é a informação, não os emojis
- Responda SEMPRE em português brasileiro
- Seja detalhado e completo — desenvolva bem suas respostas
- Quando falar de artistas, músicas ou álbuns, inclua contexto interessante (história, influências, curiosidades)
- Demonstre entusiasmo e conhecimento musical
- Use parágrafos bem estruturados
- Nunca corte a resposta no meio — sempre conclua o raciocínio
- Se não souber algo, diga claramente que não sabe responder a pergunta
- Foque apenas em assuntos que envolvam musica, nao fuja do tema, so comente de outros assuntos caso possua correlação com musica e afins
"""

SYSTEM_PROMPT_RAG = """Você é o MusicBot, um assistente musical inteligente e apaixonado por música.

Diretrizes:
- Responda SEMPRE em português brasileiro
- Use o CONTEXTO abaixo como base principal da sua resposta
- Seja detalhado e completo — desenvolva bem suas respostas com o que está no contexto
- Se o contexto não tiver informação suficiente, diga: "Não encontrei informações completas sobre isso na base de conhecimento, mas posso te ajudar com o que sei."
- Nunca corte a resposta no meio — sempre conclua o raciocínio
- Use parágrafos bem estruturados

CONTEXTO:
{contexto}"""

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
            fragmentos = self.rag_svc.buscar_contexto(mensagem, limite=3)
            usou_rag   = len(fragmentos) > 0

            if usou_rag:
                contexto      = "\n\n---\n\n".join(f["conteudo"][:300] for f in fragmentos)
                system_prompt = SYSTEM_PROMPT_RAG.format(contexto=contexto)
            else:
                system_prompt = SYSTEM_PROMPT

            conteudo_resposta = self.llm_repo.gerar_resposta(
                historico     = historico,
                system_prompt = system_prompt,
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

        # Agent não faz streaming por enquanto — cai no modo normal
        if token and _detectar_intencao_spotify(mensagem):
            resultado_agent   = run_agent(token, mensagem, historico)
            conteudo_resposta = resultado_agent["resposta"]
            midia             = resultado_agent.get("midia")

            resposta = self.chat_repo.salvar_resposta(pergunta.id, conteudo_resposta, False)

            # Simula stream para o frontend receber no mesmo formato
            def _fake_stream():
                yield conteudo_resposta

            return {
                "stream":      _fake_stream(),
                "pergunta_id": pergunta.id,
                "resposta_id": resposta.id,
                "usou_rag":    False,
                "midia":       midia,
            }

        # RAG
        fragmentos = self.rag_svc.buscar_contexto(mensagem, limite=3)
        usou_rag   = len(fragmentos) > 0

        if usou_rag:
            contexto      = "\n\n---\n\n".join(f["conteudo"][:300] for f in fragmentos)
            system_prompt = SYSTEM_PROMPT_RAG.format(contexto=contexto)
        else:
            system_prompt = SYSTEM_PROMPT

        chunks_gerados = []

        def _stream_e_acumula():
            for chunk in self.llm_repo.gerar_stream(historico, system_prompt):
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
                "id":        f"{m['role']}-{i}",
                "role":      "user" if m["role"] == "user" else "bot",
                "content":   m["content"],
                "timestamp": m["timestamp"],
            }
            for i, m in enumerate(mensagens)
        ]