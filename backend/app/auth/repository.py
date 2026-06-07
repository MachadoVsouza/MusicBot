from flask import session
from app.database.connection import get_session
from app.database.models import Usuario, SuperUsuario, Moderador


class AuthRepository:
    # ── PKCE (ainda usa session — só durante o fluxo OAuth, não para auth) ───

    def save_pkce_state(self, verifier: str, state: str) -> None:
        session["verifier"] = verifier
        session["state"]    = state

    def get_state(self) -> str | None:
        return session.get("state")

    def pop_verifier(self) -> str:
        return session.pop("verifier", "")

    # ── Tokens Spotify temporários (só durante callback) ─────────────────────

    def save_tokens_temp(self, access_token: str, refresh_token: str | None) -> None:
        session["tmp_access_token"]  = access_token
        session["tmp_refresh_token"] = refresh_token

    def get_access_token_temp(self) -> str | None:
        return session.get("tmp_access_token")

    def get_refresh_token_temp(self) -> str | None:
        return session.get("tmp_refresh_token")

    def save_spotify_usuario_id_temp(self, spotify_id: str) -> None:
        session["tmp_spotify_id"] = spotify_id

    def get_spotify_usuario_id_temp(self) -> str | None:
        return session.get("tmp_spotify_id")

    def save_spotify_profile_temp(self, spotify_type: str, display_name: str) -> None:
        session["tmp_spotify_type"] = spotify_type
        session["tmp_display_name"] = display_name

    def get_spotify_profile_temp(self) -> dict | None:
        spotify_type = session.get("tmp_spotify_type")
        display_name = session.get("tmp_display_name")
        if not spotify_type:
            return None
        return {"type": spotify_type, "display_name": display_name}

    def clear_temp(self) -> None:
        for key in ["tmp_access_token", "tmp_refresh_token", "tmp_spotify_id",
                    "tmp_spotify_type", "tmp_display_name",
                    "verifier", "state"]:
            session.pop(key, None)

    # ── DB operations ─────────────────────────────────────────────────────────

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

    def create_user_with_password(self, email: str, password_hash: str, spotify_id: str,
                                   spotify_token: str, spotify_refresh_token: str | None) -> Usuario:
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

    # ── SuperUsuario / Moderador ──────────────────────────────────────────────

    def get_moderador_by_usuario_id(self, usuario_id: str) -> Moderador | None:
        db = get_session()
        try:
            return db.query(Moderador).filter(Moderador.usuario_id == usuario_id).first()
        finally:
            db.close()

    def criar_super_usuario_e_moderador(self, usuario_id: str, nome: str) -> Moderador:
        """Cria um SuperUsuario (artista) e vincula o usuário como moderador administrador."""
        db = get_session()
        try:
            su = SuperUsuario(nome=nome)
            db.add(su)
            db.flush()

            from app.database.models import ModeradorNivel
            mod = Moderador(
                usuario_id=usuario_id,
                super_usuario_id=su.id,
                nivel=ModeradorNivel.administrador,
            )
            db.add(mod)
            db.commit()
            db.refresh(mod)
            return mod
        finally:
            db.close()

    def garantir_super_usuario_para_id_fixo(self, usuario_id: str) -> Moderador | None:
        """Garante que um ID fixo tenha SuperUsuario/Moderador, criando se necessário.
        Usado como fallback quando o Spotify callback não foi executado (ex: login email/senha)."""
        db = get_session()
        try:
            existing = db.query(Moderador).filter(Moderador.usuario_id == usuario_id).first()
            if existing:
                return existing

            from app.database.models import ModeradorNivel
            su = SuperUsuario(nome=usuario_id)  # nome padrão = spotify_id
            db.add(su)
            db.flush()

            mod = Moderador(
                usuario_id=usuario_id,
                super_usuario_id=su.id,
                nivel=ModeradorNivel.administrador,
            )
            db.add(mod)
            db.commit()
            db.refresh(mod)
            print(f"[INFO] SuperUsuario criado via fallback /me para ID fixo: {usuario_id}")
            return mod
        finally:
            db.close()
