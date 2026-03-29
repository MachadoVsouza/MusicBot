import hashlib
import base64
import secrets
import urllib.parse
import requests

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
        """Gera verifier/state, salva na sessão e retorna a URL do Spotify."""
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
        """Troca o authorization code por tokens e salva na sessão."""
        cfg  = current_app.config
        resp = requests.post(cfg["SPOTIFY_TOKEN_URL"], data={
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  cfg["REDIRECT_URI"],
            "client_id":     cfg["SPOTIFY_CLIENT_ID"],
            "code_verifier": self.repo.pop_verifier(),
        })

        if not resp.ok:
            return False

        tokens = resp.json()
        self.repo.save_tokens(
            access_token  = tokens["access_token"],
            refresh_token = tokens.get("refresh_token"),
        )
        return True

    # ── Session ───────────────────────────────────────────────────────────────

    def get_access_token(self) -> str | None:
        return self.repo.get_access_token()

    def is_authenticated(self) -> bool:
        return self.repo.is_authenticated()

    def logout(self) -> None:
        self.repo.clear()
