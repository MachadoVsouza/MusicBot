from flask import Blueprint, request
from .service import RagService
from app.core.auth_guard import require_auth
from app.core.http import success, error, not_found
from app.spotify.repository import SpotifyRepository
from app.spotify.service import SpotifyService

rag_bp = Blueprint("rag", __name__, url_prefix="/rag")


def _svc() -> RagService:
    return RagService()


def _get_spotify_id(token: str) -> str:
    return SpotifyService(SpotifyRepository(token)).get_profile()["id"]


@rag_bp.post("/documentos")
@require_auth
def submeter_documento(token: str, usuario_id: str):
    spotify_id = _get_spotify_id(token)

    if request.files.get("arquivo"):
        arquivo          = request.files["arquivo"]
        titulo           = request.form.get("titulo", arquivo.filename)
        super_usuario_id = request.form.get("super_usuario_id")
        if not super_usuario_id:
            return error("Campo 'super_usuario_id' obrigatório", 400)
        resultado = _svc().submeter_documento(
            super_usuario_id=int(super_usuario_id),
            titulo=titulo,
            conteudo="",
            tipo="pdf",
            uploaded_by=spotify_id,
            pdf_bytes=arquivo.read(),
        )
    else:
        body             = request.get_json(silent=True) or {}
        titulo           = body.get("titulo", "").strip()
        tipo             = body.get("tipo", "txt")
        super_usuario_id = body.get("super_usuario_id")
        conteudo         = body.get("conteudo", "").strip()
        url              = body.get("url", "").strip()

        if not titulo:
            return error("Campo 'titulo' obrigatório", 400)
        if not super_usuario_id:
            return error("Campo 'super_usuario_id' obrigatório", 400)
        if tipo == "link" and not url:
            return error("Campo 'url' obrigatório para tipo link", 400)
        if tipo == "txt" and not conteudo:
            return error("Campo 'conteudo' obrigatório para tipo txt", 400)

        resultado = _svc().submeter_documento(
            super_usuario_id=super_usuario_id,
            titulo=titulo,
            conteudo=conteudo,
            tipo=tipo,
            uploaded_by=spotify_id,
            url=url if tipo == "link" else None,
        )

    if "erro" in resultado:
        return error(resultado["erro"], 422)
    if resultado.get("duplicata"):
        return success(resultado, 200)
    return success(resultado, 201)


@rag_bp.get("/documentos")
@require_auth
def listar_documentos(token: str, usuario_id: str):
    status = request.args.get("status")
    return success({"documentos": _svc().listar_documentos(status)})


@rag_bp.post("/documentos/<int:documento_id>/aprovar")
@require_auth
def aprovar_documento(token: str, usuario_id: str, documento_id: int):
    spotify_id = _get_spotify_id(token)
    resultado  = _svc().aprovar_e_indexar(documento_id, spotify_id)
    if "erro" in resultado:
        return not_found(resultado["erro"])
    return success(resultado)


@rag_bp.post("/documentos/<int:documento_id>/rejeitar")
@require_auth
def rejeitar_documento(token: str, usuario_id: str, documento_id: int):
    body   = request.get_json(silent=True) or {}
    motivo = body.get("motivo", "").strip()
    if not motivo:
        return error("Campo 'motivo' obrigatório", 400)
    spotify_id = _get_spotify_id(token)
    resultado  = _svc().rejeitar_documento(documento_id, spotify_id, motivo)
    if "erro" in resultado:
        return not_found(resultado["erro"])
    return success(resultado)


@rag_bp.delete("/documentos/<int:documento_id>")
@require_auth
def deletar_documento(token: str, usuario_id: str, documento_id: int):
    ok = _svc().deletar_documento(documento_id)
    if not ok:
        return not_found("Documento não encontrado")
    return success({"ok": True})


@rag_bp.get("/buscar")
@require_auth
def buscar(token: str, usuario_id: str):
    pergunta = request.args.get("q", "").strip()
    if not pergunta:
        return error("Parâmetro 'q' obrigatório", 400)
    return success({"resultados": _svc().buscar_contexto(pergunta)})