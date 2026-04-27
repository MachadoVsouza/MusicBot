import os
import logging
from sentence_transformers import SentenceTransformer
from huggingface_hub import login

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "google/embeddinggemma-300m"


try:
    login(token=os.getenv("HUGGINGFACE_TOKEN"))
    embedder = SentenceTransformer(EMBEDDING_MODEL)
except Exception as e:
    logger.error("Erro ao carregar o modelo de embeddings: %s", e)
    embedder = None


def get_embedding(text: str) -> list[float] | None:
    if embedder is None:
        logger.error("Embedder não inicializado.")
        return None
    try:
        return embedder.encode(text).tolist()
    except Exception as e:
        logger.error("Erro ao gerar embedding: %s", e)
        return None