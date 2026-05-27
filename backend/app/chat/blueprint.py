from flask import Blueprint, request
from .service import ChatService
from app.core.auth_guard import require_auth
from app.core.http import success, error, not_found

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _svc() -> ChatService:
    return ChatService()


# ── Criar novo chat ───────────────────────────────────────────────────────────

@chat_bp.post("/")
@require_auth
def criar_chat(token: str, usuario_id: str):
    body   = request.get_json(silent=True) or {}
    titulo = body.get("titulo", "Nova conversa")

    resultado  = _svc().iniciar_chat(usuario_id, titulo)
    return success(resultado, 201)


# ── Listar chats do usuário ───────────────────────────────────────────────────

@chat_bp.get("/")
@require_auth
def listar_chats(token: str, usuario_id: str):
    return success({"chats": _svc().listar_chats(usuario_id)})


# ── Buscar mensagens de um chat específico ────────────────────────────────────

@chat_bp.get("/<int:chat_id>/messages")
@require_auth
def buscar_mensagens(token: str, usuario_id: str, chat_id: int):
    mensagens = _svc().get_mensagens(usuario_id, chat_id)
    
    if mensagens is None:
        return not_found("Chat não encontrado")
    
    return success({
        "chat_id": chat_id,
        "messages": mensagens
    })


# ── Enviar mensagem ───────────────────────────────────────────────────────────────

@chat_bp.post("/<int:chat_id>/message")
@require_auth
def enviar_mensagem(token: str, usuario_id: str, chat_id: int):
    body     = request.get_json(silent=True) or {}
    mensagem = body.get("mensagem", "").strip()

    if not mensagem:
        return error("Campo 'mensagem' obrigatório", 400, "missing_message")

    resultado  = _svc().enviar_mensagem(usuario_id, chat_id, mensagem, token=token)

    if resultado is None:
        return not_found("Chat não encontrado")

    return success(resultado)