import os
import logging
from threading import Lock

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "google/embeddinggemma-300m"

_embedder = None
_lock     = Lock()


def get_embedder():
    """Lazy loading — carrega o modelo só na primeira chamada."""
    global _embedder
    if _embedder is not None:
        return _embedder
    with _lock:
        if _embedder is not None:
            return _embedder
        try:
            from sentence_transformers import SentenceTransformer
            from huggingface_hub import login
            token = os.getenv("HUGGINGFACE_TOKEN")
            if token:
                login(token=token)
            logger.info("Carregando modelo de embeddings: %s", EMBEDDING_MODEL)
            _embedder = SentenceTransformer(EMBEDDING_MODEL)
            logger.info("Modelo de embeddings carregado.")
        except Exception:
            logger.exception("Erro ao carregar modelo de embeddings")
            return None
    return _embedder

def get_embeddings_batch(texts: list[str]) -> list[list[float]] | None:
    embedder = get_embedder()
    if not embedder:
        return None
    try:
        return embedder.encode(texts, normalize_embeddings=True, batch_size=32).tolist()
    except Exception:
        logger.exception("Erro ao gerar embeddings em batch")
        return None

def get_embedding(text: str) -> list[float] | None:
    result = get_embeddings_batch([text])
    return result[0] if result else None