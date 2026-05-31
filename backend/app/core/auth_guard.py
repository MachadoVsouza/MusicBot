import functools
import requests
from flask import current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.auth.repository import AuthRepository
from app.core.http import unauthorized


def require_auth(f):
    """
    Decorator JWT: valida o Bearer token, injeta (spotify_token, usuario_id).
    Tenta refresh automático do token Spotify se expirado.
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

        if not _is_token_valid(spotify_token):
            spotify_token = _try_refresh(repo, usuario)
            if not spotify_token:
                return unauthorized("Sessão Spotify expirada. Faça login novamente.")

        return f(spotify_token, usuario_id, *args, **kwargs)
    return wrapper


def _is_token_valid(token: str) -> bool:
    try:
        resp = requests.get(
            f"{current_app.config['SPOTIFY_API_BASE']}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code != 401
    except requests.RequestException:
        return False


def _try_refresh(repo: AuthRepository, usuario) -> str | None:
    refresh_token = usuario.spotify_refresh_token
    if not refresh_token:
        return None

    cfg = current_app.config
    resp = requests.post(cfg["SPOTIFY_TOKEN_URL"], data={
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
        "client_id":     cfg["SPOTIFY_CLIENT_ID"],
    })

    if not resp.ok:
        return None

    tokens      = resp.json()
    new_token   = tokens["access_token"]
    new_refresh = tokens.get("refresh_token", refresh_token)

    repo.update_user_spotify_tokens(usuario.spotify_id, new_token, new_refresh)
    return new_token
