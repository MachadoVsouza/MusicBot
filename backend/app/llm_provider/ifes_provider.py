"""
Provedor LLM IFES Colatina — Workstations.
"""
from flask import current_app
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel


def get_llm(stream: bool = False) -> BaseChatModel:
    """LLM via Workstations Colatina (IFES) — API compatível com OpenAI."""
    return ChatOpenAI(
        base_url    = f"{current_app.config['IFES_BASE_URL']}/v1",
        model       = current_app.config["IFES_MODEL"],
        api_key     = current_app.config["IFES_API_KEY"],
        streaming   = stream,
        temperature = 0.7,
        timeout     = 120,
        max_tokens  = 2048,
    )


def get_embeddings(texts: list[str], text: str = None) -> list[list[float]] | None:
    """Embeddings via IFES Colatina."""
    import requests
    base_url = current_app.config.get("IFES_BASE_URL", "https://workstations.chatbotintegracar.online")
    api_key  = current_app.config.get("IFES_API_KEY", "")
    model    = current_app.config.get("IFES_EMBEDDING_MODEL", "nomic-embed-text")

    if text:
        texts = [text]

    results = []
    for t in texts:
        try:
            resp = requests.post(
                f"{base_url}/api/embed",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "input": t},
                timeout=30,
            )
            resp.raise_for_status()
            emb = resp.json().get("embedding")
            if emb is None:
                emb_data = resp.json().get("embeddings")
                if emb_data and len(emb_data) > 0:
                    emb = emb_data[0]
            if emb is None:
                return None
            results.append(emb)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Embedding IFES falhou")
            return None
    return results