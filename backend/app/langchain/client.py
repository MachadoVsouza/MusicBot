"""
Cliente LangChain — delega para o provider correto baseado na preferência do usuário.
O agente Spotify sempre usa LLM local (latência baixa).
Chat e síntese RAG seguem a preferência do usuário.
"""
from langchain_core.language_models import BaseChatModel
from app.llm_provider.service import get_llm_for_user, get_agent_llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


def get_llm(stream: bool = False) -> BaseChatModel:
    """
    Retorna o LLM BASEADO NO PROVEDOR DO USUÁRIO.
    ATENÇÃO: Esta função NÃO recebe spotify_id.
    Use apenas quando o provedor não importa (ex: testes).
    Para uso real, prefira get_llm_for_user() do provider.
    """
    from flask import current_app
    from langchain_ollama import ChatOllama
    return ChatOllama(
        base_url    = current_app.config["OLLAMA_BASE_URL"],
        model       = current_app.config["OLLAMA_MODEL"],
        streaming   = stream,
        num_predict = 2048,
        temperature = 0.7,
        keep_alive  = "30m",
        timeout     = 120.0,
    )


def get_llm_for_agent(stream: bool = False) -> BaseChatModel:
    """
    Agente Spotify sempre usa LLM local (latência baixa).
    """
    return get_agent_llm(stream=stream)


def build_messages(historico: list[dict], system_prompt: str = None) -> list:
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    role_map = {"user": HumanMessage, "assistant": AIMessage}
    for msg in historico:
        cls = role_map.get(msg["role"])
        if cls:
            messages.append(cls(content=msg["content"]))
    return messages