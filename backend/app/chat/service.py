from app.chat.repository import ChatRepository
from app.langchain.repository import OllamaRepository

SYSTEM_PROMPT = """Você é o MusicBot, um assistente musical inteligente.
Você ajuda usuários a descobrir músicas, explorar artistas e entender seu gosto musical.
Responda sempre em português, de forma amigável e concisa.
Quando o usuário pedir para buscar uma música, diga que pode ajudar mas que a busca 
será implementada em breve."""


class ChatService:
    def __init__(self):
        self.chat_repo   = ChatRepository()
        self.ollama_repo = OllamaRepository()

    def iniciar_chat(self, usuario_id: str, titulo: str = "Nova conversa") -> dict:
        """Cria um novo chat para o usuário."""
        chat = self.chat_repo.criar_chat(usuario_id, titulo)
        return {"chat_id": chat.id, "titulo": chat.titulo}

    def listar_chats(self, usuario_id: str) -> list[dict]:
        chats = self.chat_repo.listar_chats(usuario_id)
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

    def enviar_mensagem(self, usuario_id: str, chat_id: int, mensagem: str) -> dict:
        """
        Fluxo completo:
        1. Verifica que o chat pertence ao usuário
        2. Busca histórico do banco
        3. Salva a pergunta
        4. Chama o Ollama com histórico + nova mensagem
        5. Salva a resposta
        6. Retorna tudo pro frontend
        """
        chat = self.chat_repo.get_chat(chat_id, usuario_id)
        if not chat:
            return None

        historico = self.chat_repo.get_historico(chat_id)

        pergunta = self.chat_repo.salvar_pergunta(chat_id, mensagem)

        historico.append({"role": "user", "content": mensagem})

        conteudo_resposta = self.ollama_repo.gerar_resposta(
            historico=historico,
            system_prompt=SYSTEM_PROMPT,
        )

        if not conteudo_resposta:
            conteudo_resposta = "Desculpe, não consegui processar sua mensagem. Tente novamente."

        resposta = self.chat_repo.salvar_resposta(pergunta.id, conteudo_resposta)

        return {
            "chat_id":     chat_id,
            "pergunta_id": pergunta.id,
            "resposta_id": resposta.id,
            "pergunta":    mensagem,
            "resposta":    conteudo_resposta,
        }