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
        provider_info = spotify_id if spotify_id else "default"
        logger.info(f"[gerar_stream] Iniciando stream - provider_user={provider_info}")
        try:
            if spotify_id:
                llm = get_llm_for_user(spotify_id, stream=True)
                logger.info(f"[gerar_stream] LLM obtida via get_llm_for_user - tipo={type(llm).__name__}")
            else:
                llm = get_llm(stream=True)
                logger.info(f"[gerar_stream] LLM obtida via get_llm - tipo={type(llm).__name__}")

            # Log da config do LLM (base_url, model) se disponível
            if hasattr(llm, 'base_url') and hasattr(llm, 'model'):
                logger.info(f"[gerar_stream] LLM config: base_url={llm.base_url}, model={llm.model}")

            messages = build_messages(historico, system_prompt)
            logger.info(f"[gerar_stream] Messages construídas - total={len(messages)}, historico_len={len(historico)}")

            chunk_count = 0
            for chunk in llm.stream(messages):
                if chunk.content:
                    chunk_count += 1
                    yield chunk.content
            logger.info(f"[gerar_stream] Stream finalizado - total_chunks={chunk_count}")
        except Exception as e:
            logger.exception(f"[gerar_stream] Erro durante o stream da LLM: {e}")
            yield f"\n\n[DEBUG: Erro no gerar_stream: {e}]"

    def gerar_resposta(self, historico: list[dict], system_prompt: str = None, spotify_id: str = None) -> str | None:
        """Versão não-streaming."""
        try:
            return "".join(self.gerar_stream(historico, system_prompt, spotify_id)) or None
        except Exception:
            logger.exception("Erro ao gerar resposta")
            return None
