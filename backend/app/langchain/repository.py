import logging
from langchain_core.messages import BaseMessage
from .client import get_llm, build_messages

logger = logging.getLogger(__name__)


class OllamaRepository:
    """Wrapper do LLM — stream é o padrão, gerar_resposta mantido por compatibilidade."""

    def gerar_stream(self, historico: list[dict], system_prompt: str = None):
        """Yielda chunks de texto conforme o LLM produz."""
        try:
            llm      = get_llm(stream=True)
            messages = build_messages(historico, system_prompt)
            for chunk in llm.stream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception:
            logger.exception("Erro durante o stream da LLM")

    def gerar_resposta(self, historico: list[dict], system_prompt: str = None) -> str | None:
        """Versão não-streaming — usa gerar_stream internamente para consistência."""
        try:
            return "".join(self.gerar_stream(historico, system_prompt)) or None
        except Exception:
            logger.exception("Erro ao gerar resposta")
            return None