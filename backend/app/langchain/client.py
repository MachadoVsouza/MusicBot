from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from flask import current_app


def get_llm(stream: bool = False) -> BaseChatModel:
    return ChatOllama(
        base_url    = current_app.config["OLLAMA_BASE_URL"],
        model       = current_app.config["OLLAMA_MODEL"],
        streaming   = stream,
        num_predict = 2048,
        temperature = 0.7,
        keep_alive  = "30m",
        timeout     = 120.0,
    )


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