import functools
import requests
from flask import current_app
from app.auth.repository import AuthRepository
from app.core.http import unauthorized


def require_auth(f):
    """
    Decorator que garante que a requisição tem um access_token válido.
    Tenta refresh automático se o token estiver expirado.
    Injeta o token como primeiro argumento da função decorada.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        repo  = AuthRepository()
        token = repo.get_access_token()

        if not token:
            return unauthorized()

        # Verifica se o token ainda é válido
        if not _is_token_valid(token):
            token = _try_refresh(repo)
            if not token:
                repo.clear()
                return unauthorized("Sessão expirada. Faça login novamente.")

        return f(token, *args, **kwargs)
    return wrapper


def _is_token_valid(token: str) -> bool:
    """Faz uma chamada leve à API para verificar o token."""
    try:
        resp = requests.get(
            f"{current_app.config['SPOTIFY_API_BASE']}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code != 401
    except requests.RequestException:
        return False


def _try_refresh(repo: AuthRepository) -> str | None:
    """Tenta obter um novo access_token usando o refresh_token."""
    refresh_token = repo.get_refresh_token()
    if not refresh_token:
        return None

    cfg  = current_app.config
    resp = requests.post(cfg["SPOTIFY_TOKEN_URL"], data={
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
        "client_id":     cfg["SPOTIFY_CLIENT_ID"],
    })

    if not resp.ok:
        return None

    tokens        = resp.json()
    new_token     = tokens["access_token"]
    new_refresh   = tokens.get("refresh_token", refresh_token)  # Spotify nem sempre retorna novo refresh

    repo.save_tokens(new_token, new_refresh)
    return new_token
