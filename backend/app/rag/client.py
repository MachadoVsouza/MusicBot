import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "nomic-embed-text"  # modelo leve de embeddings, roda local no Ollama


def get_embedding(text: str) -> list[float] | None:
    """
    Gera o embedding de um texto usando o Ollama local.
    Retorna uma lista de 768 floats.
    """
    try:
        resp = requests.post(
            f"{current_app.config['OLLAMA_BASE_URL']}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except Exception as e:
        logger.error("Erro ao gerar embedding: %s", e)
        return None
