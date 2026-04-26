from .repository import ChatRepository
from app.langchain.repository import OllamaRepository
from app.rag.service import RagService

SYSTEM_PROMPT = """Você é o MusicBot, um assistente musical inteligente.
Você ajuda usuários a descobrir músicas, explorar artistas e entender seu gosto musical.
Responda sempre em português, de forma amigável e concisa.
Quando o usuário pedir para buscar uma música, diga que pode ajudar mas que a busca 
será implementada em breve."""

SYSTEM_PROMPT_RAG = """Você é o MusicBot, um assistente musical inteligente.
Responda sempre em português, de forma amigável e concisa.
Use as informações do CONTEXTO abaixo para responder. 
Se a resposta não estiver no contexto, diga que não encontrou a informação.

CONTEXTO:
{contexto}"""


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

    def enviar_mensagem(self, spotify_id: str, chat_id: int, mensagem: str) -> dict | None:
        chat = self.chat_repo.get_chat(chat_id, spotify_id)
        if not chat:
            return None

        # Busca contexto RAG para a pergunta
        fragmentos  = self.rag_svc.buscar_contexto(mensagem, limite=3)
        usou_rag    = len(fragmentos) > 0

        # Monta o historico
        historico = self.chat_repo.get_historico(chat_id)
        pergunta  = self.chat_repo.salvar_pergunta(chat_id, mensagem)
        historico.append({"role": "user", "content": mensagem})

        # Escolhe o system prompt com ou sem RAG
        if usou_rag:
            contexto      = "\n\n---\n\n".join(f["conteudo"] for f in fragmentos)
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

        # Salva quais fragmentos foram usados na resposta
        if usou_rag:
            self.rag_svc.salvar_fontes(resposta.id, [f["fragmento_id"] for f in fragmentos])

        return {
            "chat_id":     chat_id,
            "pergunta_id": pergunta.id,
            "resposta_id": resposta.id,
            "pergunta":    mensagem,
            "resposta":    conteudo_resposta,
            "usou_rag":    usou_rag,
            "fontes":      fragmentos if usou_rag else [],
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
