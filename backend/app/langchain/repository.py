import logging
from langchain_core.messages import BaseMessage
from .client import get_llm, get_llm_for_agent, build_messages
from app.llm_provider.service import get_llm_for_user

logger = logging.getLogger(__name__)


class OllamaRepository:
    """Wrapper do LLM — stream é o padrão, gerar_resposta mantido por compatibilidade."""

    def gerar_stream(self, historico: list[dict], system_prompt: str = None, spotify_id: str = None):
        """Yielda chunks de texto conforme o LLM produz.
        Se spotify_id for informado, usa o provider preferido do usuário.
        """
        try:
            if spotify_id:
                llm = get_llm_for_user(spotify_id, stream=True)
            else:
                llm = get_llm(stream=True)
            messages = build_messages(historico, system_prompt)
            for chunk in llm.stream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception:
            logger.exception("Erro durante o stream da LLM")

    def gerar_resposta(self, historico: list[dict], system_prompt: str = None, spotify_id: str = None) -> str | None:
        """Versão não-streaming."""
        try:
            return "".join(self.gerar_stream(historico, system_prompt, spotify_id)) or None
        except Exception:
            logger.exception("Erro ao gerar resposta")
            return None
