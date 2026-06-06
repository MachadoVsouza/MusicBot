"""
Client de embeddings — delega para o provider correto via llm_provider.service.
"""
import logging
from typing import Optional
from app.llm_provider.service import get_embeddings

logger = logging.getLogger(__name__)


def get_embedding(text: str, spotify_id: str = None) -> Optional[list[float]]:
    """Gera embedding para um texto. Se spotify_id for informado, respeita o provider do usuário."""
    result = get_embeddings([], spotify_id=spotify_id, text=text)
    if result:
        return result[0]
    return None


def get_embeddings_batch(texts: list[str], spotify_id: str = None) -> Optional[list[list[float]]]:
    """Gera embeddings para uma lista de textos."""
    return get_embeddings(texts, spotify_id=spotify_id)
