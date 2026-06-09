import functools
import time
import requests
from flask import current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.auth.repository import AuthRepository
from app.core.http import unauthorized, forbidden

# Cache em memória para _is_token_valid (evita chamada externa a cada request)
# Estrutura: { token_hash: (is_valid: bool, timestamp: float) }
_token_valid_cache: dict[str, tuple[bool, float]] = {}
TOKEN_CACHE_TTL = 300  # 5 minutos


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

        if not spotify_token:
            print(f"[require_auth] Usuário {usuario_id} não tem spotify_token salvo")
            return unauthorized("Token Spotify não encontrado. Faça login novamente.")

        if not _is_token_valid(spotify_token):
            print(f"[require_auth] Token Spotify inválido para {usuario_id}, tentando refresh...")
            spotify_token = _try_refresh(repo, usuario)
            if not spotify_token:
                print(f"[require_auth] Refresh falhou para {usuario_id}")
                return unauthorized("Sessão Spotify expirada. Faça login novamente.")
            print(f"[require_auth] Token Spotify renovado com sucesso para {usuario_id}")

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


def _is_token_valid(token: str) -> bool:
    """Verifica se o token Spotify é válido, com cache TTL de 5 minutos."""
    # Usa os primeiros 8 caracteres do token como chave de cache
    cache_key = token[:32] if len(token) >= 32 else token
    now = time.time()

    if cache_key in _token_valid_cache:
        is_valid, timestamp = _token_valid_cache[cache_key]
        if now - timestamp < TOKEN_CACHE_TTL:
            return is_valid
        # Cache expirado, remove
        del _token_valid_cache[cache_key]

    try:
        resp = requests.get(
            f"{current_app.config['SPOTIFY_API_BASE']}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        is_valid = resp.status_code != 401
        _token_valid_cache[cache_key] = (is_valid, now)
        if not is_valid:
            print(f"[_is_token_valid] Token inválido, status={resp.status_code}, body={resp.text[:200]}")
        return is_valid
    except requests.RequestException as e:
        print(f"[_is_token_valid] Erro de rede ao validar token: {e}")
        # Em caso de erro de rede, assume válido (melhor tentar usar do que barrar)
        return True


def _try_refresh(repo: AuthRepository, usuario) -> str | None:
    refresh_token = usuario.spotify_refresh_token
    if not refresh_token:
        print("[_try_refresh] Sem refresh_token salvo")
        return None

    cfg = current_app.config
    client_id = cfg.get("SPOTIFY_CLIENT_ID", "")
    client_secret = cfg.get("SPOTIFY_CLIENT_SECRET", "")

    print(f"[_try_refresh] Tentando refresh para usuario {usuario.spotify_id}")
    print(f"[_try_refresh] client_id={client_id[:8]}... client_secret={'***' if client_secret else 'VAZIO!'}")

    try:
        resp = requests.post(
            cfg["SPOTIFY_TOKEN_URL"],
            data={
                "grant_type":    "refresh_token",
                "refresh_token": refresh_token,
                "client_id":     client_id,
                "client_secret": client_secret,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[_try_refresh] Erro de rede: {e}")
        return None

    if not resp.ok:
        print(f"[_try_refresh] Spotify retornou {resp.status_code}: {resp.text[:300]}")
        return None

    tokens      = resp.json()
    new_token   = tokens["access_token"]
    new_refresh = tokens.get("refresh_token", refresh_token)

    print(f"[_try_refresh] Refresh bem-sucedido, novo token: {new_token[:10]}...")
    repo.update_user_spotify_tokens(usuario.spotify_id, new_token, new_refresh)
    return new_token
