"""
Provedor LLM Local — Ollama.
"""
from flask import current_app
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel


def get_llm(stream: bool = False) -> BaseChatModel:
    """LLM via Ollama local."""
    return ChatOllama(
        base_url    = current_app.config["OLLAMA_BASE_URL"],
        model       = current_app.config["OLLAMA_MODEL"],
        streaming   = stream,
        num_predict = 2048,
        temperature = 0.7,
        keep_alive  = "30m",
        timeout     = 120.0,
    )


def get_embeddings(texts: list[str], text: str = None) -> list[list[float]] | None:
    """Embeddings via Ollama local."""
    import requests
    base_url = current_app.config.get("OLLAMA_BASE_URL", "http://ollama:11434")
    model = "nomic-embed-text"

    if text:
        texts = [text]

    results = []
    for t in texts:
        try:
            resp = requests.post(
                f"{base_url}/api/embeddings",
                json={"model": model, "prompt": t},
                timeout=30,
            )
            resp.raise_for_status()
            emb = resp.json().get("embedding")
            if emb is None:
                return None
            results.append(emb)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Embedding local falhou")
            return None
    return results