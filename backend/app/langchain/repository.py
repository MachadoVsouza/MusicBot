import logging
from .client import get_llm, build_messages

logger = logging.getLogger(__name__)


class OllamaRepository:
    #apagar depois
    def gerar_resposta(self, historico: list[dict], system_prompt: str = None) -> str | None:
        try:
            llm      = get_llm(stream=False)
            messages = build_messages(historico, system_prompt)
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.exception("Erro ao chamar LLM na geração normal")
            return None

    def gerar_stream(self, historico: list[dict], system_prompt: str = None):
        """
        Gerador que yielda chunks de texto conforme o LLM produz.
        Uso: for chunk in repo.gerar_stream(...): yield chunk
        """
        try:
            llm      = get_llm(stream=True)
            messages = build_messages(historico, system_prompt)
            for chunk in llm.stream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.exception("Erro durante o stream da LLM")
