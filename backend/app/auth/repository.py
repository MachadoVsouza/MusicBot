from flask import session
from app.database.connection import get_session
from app.database.models import Usuario

class AuthRepository:
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

    def save_spotify_usuario_id(self, spotify_id: str) -> None:
        session["spotify_usuario_id"] = spotify_id

    def get_spotify_usuario_id(self) -> str | None:
        return session.get("spotify_usuario_id")

    def is_authenticated(self) -> bool:
        return "access_token" in session and "usuario_id" in session

    def clear(self) -> None:
        session.clear()

    def save_usuario_id(self, usuario_id: str) -> None:
        session["usuario_id"] = usuario_id

    def get_usuario_id(self) -> str | None:
        return session.get("usuario_id")

    # ── DB operations ─────────────────────────────────────────────────────────

    def get_or_create_usuario_by_spotify(self, spotify_id: str, access_token: str = None, refresh_token: str = None) -> Usuario:
        db = get_session()
        try:
            usuario = db.query(Usuario).filter(Usuario.spotify_id == spotify_id).first()
            
            if not usuario:
                usuario = Usuario(
                    spotify_id=spotify_id,
                    spotify_token=access_token,
                    spotify_refresh_token=refresh_token,
                )
                db.add(usuario)
                db.commit()
                db.refresh(usuario)
            
            return usuario
        finally:
            db.close()

    def get_usuario_by_spotify_id(self, spotify_id: str) -> Usuario | None:
        db = get_session()
        try:
            return db.query(Usuario).filter(Usuario.spotify_id == spotify_id).first()
        finally:
            db.close()

    def get_usuario_by_email(self, email: str) -> Usuario | None:
        db = get_session()
        try:
            return db.query(Usuario).filter(Usuario.email == email).first()
        finally:
            db.close()

    def update_user_spotify_tokens(self, spotify_id: str, access_token: str, refresh_token: str | None) -> None:
        db = get_session()
        try:
            usuario = db.get(Usuario, spotify_id)
            if usuario:
                usuario.spotify_token = access_token
                usuario.spotify_refresh_token = refresh_token
                db.commit()
        finally:
            db.close()

    def create_user_with_password(self, email: str, password_hash: str, spotify_id: str, spotify_token: str, spotify_refresh_token: str | None) -> Usuario:
        db = get_session()
        try:
            usuario = db.query(Usuario).filter(Usuario.spotify_id == spotify_id).first()
            
            if usuario:
                usuario.email = email
                usuario.password_hash = password_hash
                usuario.spotify_token = spotify_token
                usuario.spotify_refresh_token = spotify_refresh_token
            else:
                usuario = Usuario(
                    spotify_id=spotify_id,
                    email=email,
                    password_hash=password_hash,
                    spotify_token=spotify_token,
                    spotify_refresh_token=spotify_refresh_token,
                )
                db.add(usuario)
            
            db.commit()
            db.refresh(usuario)
            return usuario
        finally:
            db.close()

    def update_user_password(self, spotify_id: str, password_hash: str) -> None:
        db = get_session()
        try:
            usuario = db.get(Usuario, spotify_id)
            if usuario:
                usuario.password_hash = password_hash
                db.commit()
        finally:
            db.close()
