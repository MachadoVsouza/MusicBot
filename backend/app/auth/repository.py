from flask import session


class AuthRepository:
    """Responsável por persistir e recuperar dados de autenticação na sessão."""

    def save_tokens(self, access_token: str, refresh_token: str | None) -> None:
        session["access_token"]  = access_token
        session["refresh_token"] = refresh_token

    def save_pkce_state(self, verifier: str, state: str) -> None:
        session["verifier"] = verifier
        session["state"]    = state

    def get_access_token(self) -> str | None:
        return session.get("access_token")

    def get_refresh_token(self) -> str | None:
        return session.get("refresh_token")

    def pop_verifier(self) -> str:
        return session.pop("verifier", "")

    def get_state(self) -> str | None:
        return session.get("state")

    def is_authenticated(self) -> bool:
        return "access_token" in session

    def clear(self) -> None:
        session.clear()
