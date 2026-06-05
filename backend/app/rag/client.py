"""
Client de embeddings usando a API do próprio Ollama (/api/embeddings).
Substitui SentenceTransformers para evitar OOM (modelo ~600MB desnecessário).
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "gemma4:e4b")


def _get_ollama_embedding(text: str) -> Optional[list[float]]:
    """Chama /api/embeddings do Ollama para uma única string."""
    import requests
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("embedding")
    except Exception:
        logger.exception("Erro ao gerar embedding via Ollama")
        return None


def get_embedding(text: str) -> Optional[list[float]]:
    """Gera embedding para um texto."""
    return _get_ollama_embedding(text)


def get_embeddings_batch(texts: list[str]) -> Optional[list[list[float]]]:
    """Gera embeddings para uma lista de textos (chamada individual por ora)."""
    results = []
    for t in texts:
        emb = _get_ollama_embedding(t)
        if emb is None:
            return None
        results.append(emb)
    return results