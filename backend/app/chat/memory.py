"""
Memory do LangChain — substitui o histórico manual por RunnableWithMessageHistory.
Usa o banco PostgreSQL via ChatMessageHistory para persistir o histórico
de cada conversa e gerenciar automaticamente a janela de contexto.
"""
import logging
from typing import Optional
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from app.database.connection import get_session
from app.database.models import Pergunta, Resposta

logger = logging.getLogger(__name__)

# Cache de históricos por chat_id (evita recarregar do banco a cada chamada)
_history_cache: dict[str, ChatMessageHistory] = {}


class DbChatMessageHistory(BaseChatMessageHistory):
    """
    ChatMessageHistory que carrega/salva do banco PostgreSQL.
    Em vez de usar Redis ou memória volátil, persiste no modelo
    Pergunta/Resposta já existente.
    """

    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self._messages: list[BaseMessage] | None = None

    @property
    def messages(self) -> list[BaseMessage]:
        if self._messages is None:
            self._messages = self._load_from_db()
        return self._messages

    @messages.setter
    def messages(self, value: list[BaseMessage]):
        self._messages = value

    def _load_from_db(self) -> list[BaseMessage]:
        """Carrega o histórico do banco."""
        db = get_session()
        try:
            perguntas = db.query(Pergunta).filter(
                Pergunta.chat_id == self.chat_id,
            ).order_by(Pergunta.created_at.asc()).limit(50).all()

            messages: list[BaseMessage] = []
            for p in perguntas:
                messages.append(HumanMessage(content=p.conteudo))
                if p.resposta:
                    messages.append(AIMessage(content=p.resposta.conteudo))
            return messages
        finally:
            db.close()

    def add_message(self, message: BaseMessage) -> None:
        """Adiciona uma mensagem ao histórico em memória."""
        if self._messages is None:
            self._messages = self._load_from_db()
        self._messages.append(message)

    def add_user_message(self, content: str) -> None:
        self.add_message(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        self.add_message(AIMessage(content=content))

    def clear(self) -> None:
        self._messages = []
        if str(self.chat_id) in _history_cache:
            del _history_cache[str(self.chat_id)]


def get_chat_history(session_id: str) -> BaseChatMessageHistory:
    """
    Função para usar com RunnableWithMessageHistory.
    session_id = str(chat_id)
    """
    if session_id not in _history_cache:
        _history_cache[session_id] = DbChatMessageHistory(int(session_id))
    return _history_cache[session_id]


def get_history_messages(chat_id: int, limite: int = 20) -> list[dict]:
    """
    Retorna o histórico no formato antigo para compatibilidade.
    """
    history = DbChatMessageHistory(chat_id)
    messages = history.messages[-limite * 2:]  # user + assistant = 2 por turno
    return [
        {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
        for m in messages
    ]