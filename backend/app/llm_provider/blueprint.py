"""
Blueprint para gerenciar o provedor LLM do usuário (local vs ifes).
"""
from flask import Blueprint, request
from app.core.auth_guard import require_auth
from app.core.http import success, error
from app.database.connection import get_session
from app.database.models import Usuario

llm_provider_bp = Blueprint("llm_provider", __name__, url_prefix="/llm-provider")


@llm_provider_bp.get("/")
@require_auth
def get_provider(token: str, usuario_id: str):
    """Retorna o provedor atual do usuário."""
    db = get_session()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario:
            return success({"provider": "local", "disponiveis": ["local", "ifes"]})
        return success({
            "provider": usuario.llm_provider or "local",
            "disponiveis": ["local", "ifes"],
        })
    finally:
        db.close()


@llm_provider_bp.post("/")
@require_auth
def set_provider(token: str, usuario_id: str):
    """Altera o provedor LLM do usuário."""
    body = request.get_json(silent=True) or {}
    provider = body.get("provider", "").strip()

    if provider not in ("local", "ifes"):
        return error("Provedor inválido. Use 'local' ou 'ifes'.", 400)

    db = get_session()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario:
            return error("Usuário não encontrado", 404)
        usuario.llm_provider = provider
        db.commit()
        return success({"provider": provider})
    finally:
        db.close()