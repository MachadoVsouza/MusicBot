from app.database.connection import get_session
from app.database.models import Chat, Pergunta, Resposta, Usuario


class ChatRepository:

    def get_or_create_usuario(self, usuario_id: str) -> Usuario:
        """Retorna o usuário pelo ID. Note: Usuario deve ser criado via auth flow."""
        db = get_session()
        try:
            usuario = db.get(Usuario, usuario_id)
            if not usuario:
                raise ValueError(f"Usuario {usuario_id} não encontrado. Crie via auth flow.")
            return usuario
        finally:
            db.close()

    def criar_chat(self, usuario_id: str, titulo: str = "Nova conversa") -> Chat:
        db = get_session()
        try:
            chat = Chat(usuario_id=usuario_id, titulo=titulo)
            db.add(chat)
            db.commit()
            db.refresh(chat)
            return chat
        finally:
            db.close()

    def get_chat(self, chat_id: int, usuario_id: str) -> Chat | None:
        db = get_session()
        try:
            return db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.usuario_id == usuario_id,
            ).first()
        finally:
            db.close()

    def listar_chats(self, usuario_id: str) -> list[Chat]:
        db = get_session()
        try:
            return db.query(Chat).filter(
                Chat.usuario_id == usuario_id,
            ).order_by(Chat.updated_at.desc()).all()
        finally:
            db.close()

    def salvar_pergunta(self, chat_id: int, conteudo: str) -> Pergunta:
        db = get_session()
        try:
            pergunta = Pergunta(chat_id=chat_id, conteudo=conteudo)
            db.add(pergunta)
            db.commit()
            db.refresh(pergunta)
            return pergunta
        finally:
            db.close()

    def salvar_resposta(self, pergunta_id: int, conteudo: str, usou_rag: bool = False) -> Resposta:
        db = get_session()
        try:
            resposta = Resposta(
                pergunta_id=pergunta_id,
                conteudo=conteudo,
                usou_rag=usou_rag,
            )
            db.add(resposta)
            db.commit()
            db.refresh(resposta)
            return resposta
        finally:
            db.close()

    def get_historico(self, chat_id: int, limite: int = 20) -> list[dict]:
        """
        Retorna o histórico no formato que o Ollama espera:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        db = get_session()
        try:
            perguntas = db.query(Pergunta).filter(
                Pergunta.chat_id == chat_id,
            ).order_by(Pergunta.created_at.asc()).limit(limite).all()

            historico = []
            for p in perguntas:
                historico.append({"role": "user", "content": p.conteudo})
                if p.resposta:
                    historico.append({"role": "assistant", "content": p.resposta.conteudo})
            return historico
        finally:
            db.close()
    def get_mensagens_completas(self, chat_id: int) -> list[dict]:
        """
        Retorna as mensagens no formato que o frontend espera:
        [{"role": "user"|"assistant", "content": "...", "timestamp": "..."}]
        """
        db = get_session()
        try:
            perguntas = db.query(Pergunta).filter(
                Pergunta.chat_id == chat_id,
            ).order_by(Pergunta.created_at.asc()).all()

            mensagens = []
            for p in perguntas:
                mensagens.append({
                    "role":        "user",
                    "content":     p.conteudo,
                    "timestamp":   p.created_at.isoformat(),
                    "pergunta_id": p.id,
                })
                if p.resposta:
                    mensagens.append({
                        "role":        "bot",
                        "content":     p.resposta.conteudo,
                        "timestamp":   p.resposta.created_at.isoformat(),
                        "resposta_id": p.resposta.id,
                        "usou_rag":    p.resposta.usou_rag,
                    })
            return mensagens
        finally:
            db.close()