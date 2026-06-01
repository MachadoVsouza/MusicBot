import hashlib
import base64
import secrets
import urllib.parse
import requests
from werkzeug.security import generate_password_hash

from flask import current_app
from .repository import AuthRepository


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    # ── PKCE helpers ──────────────────────────────────────────────────────────

    def _make_verifier(self) -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()

    def _make_challenge(self, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    # ── Login ─────────────────────────────────────────────────────────────────

    def build_auth_url(self) -> str:
        verifier  = self._make_verifier()
        challenge = self._make_challenge(verifier)
        state     = secrets.token_urlsafe(16)

        self.repo.save_pkce_state(verifier, state)

        cfg    = current_app.config
        params = urllib.parse.urlencode({
            "client_id":             cfg["SPOTIFY_CLIENT_ID"],
            "response_type":         "code",
            "redirect_uri":          cfg["REDIRECT_URI"],
            "scope":                 cfg["SPOTIFY_SCOPES"],
            "state":                 state,
            "code_challenge_method": "S256",
            "code_challenge":        challenge,
        })
        return f"{cfg['SPOTIFY_AUTH_URL']}?{params}"

    def validate_state(self, received_state: str) -> bool:
        return received_state == self.repo.get_state()

    # ── Callback ──────────────────────────────────────────────────────────────

    def exchange_code(self, code: str) -> bool:
        cfg = current_app.config
        try:
            resp = requests.post(cfg["SPOTIFY_TOKEN_URL"], data={
                "grant_type":    "authorization_code",
                "code":          code,
                "redirect_uri":  cfg["REDIRECT_URI"],
                "client_id":     cfg["SPOTIFY_CLIENT_ID"],
                "client_secret": cfg["SPOTIFY_CLIENT_SECRET"],
                "code_verifier": self.repo.pop_verifier(),
            })
            if not resp.ok:
                return False
            tokens = resp.json()
            self.repo.save_tokens_temp(
                access_token  = tokens.get("access_token"),
                refresh_token = tokens.get("refresh_token"),
            )
            return True
        except Exception:
            return False

    def fetch_spotify_profile(self, access_token: str) -> dict | None:
        try:
            resp = requests.get(
                "https://api.spotify.com/v1/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            print(f"[DEBUG] fetch_spotify_profile status={resp.status_code}")
            if not resp.ok:
                print(f"[ERROR] Spotify /me retornou: {resp.status_code} {resp.text}")
                return None
            return resp.json()
        except Exception:
            print(f"[ERROR] fetch_spotify_profile exception: {e}")
        return None

    def handle_spotify_callback(self) -> dict:
        access_token  = self.repo.get_access_token_temp()
        refresh_token = self.repo.get_refresh_token_temp()

        if not access_token:
            return {"flow": None}

        profile = self.fetch_spotify_profile(access_token)
        if not profile:
            return {"flow": None}

        spotify_id = profile.get("id")
        if not spotify_id:
            return {"flow": None}

        self.repo.save_spotify_usuario_id_temp(spotify_id)

        usuario = self.repo.get_usuario_by_spotify_id(spotify_id)
        if usuario:
            self.repo.update_user_spotify_tokens(spotify_id, access_token, refresh_token)
            self.repo.clear_temp()
            return {"flow": "login", "spotify_id": spotify_id, "profile": profile}
        else:
            return {"flow": "register", "spotify_id": spotify_id, "profile": profile}

    # ── Registration ──────────────────────────────────────────────────────────

    def register_user(self, email: str, password: str) -> dict:
        spotify_id    = self.repo.get_spotify_usuario_id_temp()
        access_token  = self.repo.get_access_token_temp()
        refresh_token = self.repo.get_refresh_token_temp()

        if not spotify_id or not access_token:
            return {"success": False, "message": "Tokens do Spotify não encontrados.", "code": "missing_spotify_tokens"}

        try:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        except Exception as e:
            return {"success": False, "message": str(e), "code": "password_hash_error"}

        try:
            usuario = self.repo.create_user_with_password(
                email=email,
                password_hash=password_hash,
                spotify_id=spotify_id,
                spotify_token=access_token,
                spotify_refresh_token=refresh_token,
            )
            self.repo.clear_temp()
            return {"success": True, "usuario_id": usuario.spotify_id}
        except Exception as e:
            return {"success": False, "message": str(e), "code": "user_creation_error"}

    def login_with_password(self, email: str, password: str) -> dict:
        from werkzeug.security import check_password_hash
        try:
            usuario = self.repo.get_usuario_by_email(email)
            if not usuario:
                return {"success": False, "message": "Email ou senha inválidos"}
            if not usuario.password_hash:
                return {"success": False, "message": "Use Spotify para fazer login."}
            if not check_password_hash(usuario.password_hash, password):
                return {"success": False, "message": "Email ou senha inválidos"}
            return {"success": True, "usuario_id": usuario.spotify_id}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def set_user_password(self, usuario_id: str, password: str) -> dict:
        try:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            self.repo.update_user_password(usuario_id, password_hash)
            return {"success": True, "message": "Senha definida com sucesso!"}
        except Exception as e:
            return {"success": False, "message": str(e), "code": "password_update_error"}

    def get_access_token(self) -> str | None:
        return self.repo.get_access_token_temp()
