"""
Serviço de provedor LLM — decide qual provedor usar baseado na preferência do usuário.
Roteia entre local_provider.py e ifes_provider.py.
"""
from flask import current_app
from langchain_core.language_models import BaseChatModel
from app.database.connection import get_session
from app.database.models import Usuario


def get_user_provider(spotify_id: str) -> str:
    """Busca a preferência do usuário no banco. Fallback: env var."""
    try:
        db = get_session()
        try:
            usuario = db.get(Usuario, spotify_id)
            if usuario and usuario.llm_provider in ("local", "ifes"):
                return usuario.llm_provider
        finally:
            db.close()
    except Exception:
        pass
    return current_app.config.get("LLM_PROVIDER", "local")


def get_llm_for_user(spotify_id: str, stream: bool = False) -> BaseChatModel:
    """Retorna o LLM conforme a preferência do usuário."""
    provider = get_user_provider(spotify_id)
    if provider == "ifes":
        from . import ifes_provider
        return ifes_provider.get_llm(stream)
    from . import local_provider
    return local_provider.get_llm(stream)


def get_agent_llm(stream: bool = False) -> BaseChatModel:
    """Agente Spotify sempre usa LLM local (latência baixa)."""
    from . import local_provider
    return local_provider.get_llm(stream)


def get_llm_for_sintese(spotify_id: str) -> BaseChatModel:
    """Síntese RAG segue a preferência do usuário."""
    return get_llm_for_user(spotify_id, stream=False)


def get_embeddings(texts: list[str], spotify_id: str = None, text: str = None):
    """Gera embeddings conforme o provider do usuário."""
    provider = "local"
    if spotify_id:
        provider = get_user_provider(spotify_id)

    if provider == "ifes":
        from . import ifes_provider
        return ifes_provider.get_embeddings(texts, text)
    from . import local_provider
    return local_provider.get_embeddings(texts, text)
