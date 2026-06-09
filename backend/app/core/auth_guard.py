import functools
import requests
from datetime import datetime, timezone
from flask import current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.auth.repository import AuthRepository
from app.core.http import unauthorized, forbidden


def require_auth(f):
    """
    Decorator JWT: valida o Bearer token, injeta (spotify_token, usuario_id).
    Tenta refresh automático do token Spotify se expirado.
    Valida token Spotify localmente via spotify_token_expires_at (zero chamadas à API Spotify).
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return unauthorized("Token inválido ou ausente")

        usuario_id = get_jwt_identity()
        if not usuario_id:
            return unauthorized()

        repo = AuthRepository()
        usuario = repo.get_usuario_by_spotify_id(usuario_id)
        if not usuario:
            return unauthorized("Usuário não encontrado")

        spotify_token = usuario.spotify_token

        if not _is_token_valid(usuario):
            spotify_token = _try_refresh(repo, usuario)
            if not spotify_token:
                return unauthorized("Sessão Spotify expirada. Faça login novamente.")

        return f(spotify_token, usuario_id, *args, **kwargs)
    return wrapper


def require_moderator(f):
    """
    Decorator que exige autenticação JWT + role de moderador.
    Injeta (spotify_token, usuario_id) como require_auth.
    """
    @functools.wraps(f)
    @require_auth
    def wrapper(spotify_token: str, usuario_id: str, *args, **kwargs):
        repo = AuthRepository()
        moderador = repo.get_moderador_by_usuario_id(usuario_id)
        super_ids = current_app.config.get("SUPER_USER_IDS", [])

        print(f"[DEBUG require_moderator] usuario_id={usuario_id}, SUPER_USER_IDS={super_ids}, moderador={moderador is not None}")

        if not moderador and usuario_id not in super_ids:
            return forbidden("Acesso restrito a moderadores")

        return f(spotify_token, usuario_id, *args, **kwargs)
    return wrapper


def _is_token_valid(usuario) -> bool:
    """
    Validação local do token Spotify usando spotify_token_expires_at.
    Zero chamadas à API Spotify — evita consumo de rate limit.
    Se expires_at for None (dados antigos), assume válido e deixa
    o erro 401 real do Spotify disparar o refresh em _try_refresh.
    """
    expires_at = getattr(usuario, 'spotify_token_expires_at', None)
    if expires_at is None:
        # Fallback: token sem data de expiração (usuário antigo)
        # Assume válido — se estiver expirado, o Spotify retornará 401
        # e o fluxo de erro do endpoint específico lidará com isso
        return True
    return datetime.now(timezone.utc) < expires_at


def _try_refresh(repo: AuthRepository, usuario) -> str | None:
    refresh_token = usuario.spotify_refresh_token
    if not refresh_token:
        return None

    cfg = current_app.config
    resp = requests.post(cfg["SPOTIFY_TOKEN_URL"], data={
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
        "client_id":     cfg["SPOTIFY_CLIENT_ID"],
        "client_secret": cfg["SPOTIFY_CLIENT_SECRET"],
    })

    if not resp.ok:
        return None

    tokens      = resp.json()
    new_token   = tokens["access_token"]
    new_refresh = tokens.get("refresh_token", refresh_token)
    expires_in  = tokens.get("expires_in")

    repo.update_user_spotify_tokens(usuario.spotify_id, new_token, new_refresh, expires_in)
    return new_token