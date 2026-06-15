import hashlib
import base64
import secrets
import urllib.parse
import smtplib
from datetime import timedelta
import requests
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash

from flask import current_app
from flask_jwt_extended import create_access_token, decode_token
from .repository import AuthRepository
from app.core.audit import registrar_auditoria


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
            # Verifica se é artista Spotify ou ID fixo → garante SuperUsuario
            self._verificar_e_criar_super_usuario(spotify_id, profile)
            self.repo.clear_temp()
            return {"flow": "login", "spotify_id": spotify_id, "profile": profile}
        else:
            # Salva dados do perfil na sessão temporária para o registro
            self.repo.save_spotify_profile_temp(
                spotify_type=profile.get("type", "user"),
                display_name=profile.get("display_name", ""),
            )
            return {"flow": "register", "spotify_id": spotify_id, "profile": profile}

    def _verificar_e_criar_super_usuario(self, spotify_id: str, profile: dict) -> None:
        """Se o perfil Spotify for do tipo 'artist' OU for um ID fixo de super usuário,
        cria automaticamente um SuperUsuario e vincula como moderador administrador."""
        tipo_conta = profile.get("type")  # "user" ou "artist"
        is_fixed = spotify_id in current_app.config.get("SUPER_USER_IDS", [])
        if tipo_conta != "artist" and not is_fixed:
            return

        moderador = self.repo.get_moderador_by_usuario_id(spotify_id)
        if moderador:
            return  # Já é moderador

        nome = profile.get("display_name") or profile.get("id") or "Artista"
        mod = self.repo.criar_super_usuario_e_moderador(spotify_id, nome)
        motivo = "ID fixo" if is_fixed else f"tipo Spotify: {tipo_conta}"
        print(f"[INFO] SuperUsuario criado automaticamente para {spotify_id} ({nome}) - {motivo}")

        # Registra auditoria
        registrar_auditoria(
            usuario_id=spotify_id,
            acao="moderador.criar_automatico",
            entidade="moderador",
            entidade_id=mod.id,
            detalhes={"super_usuario_id": mod.super_usuario_id, "nivel": "administrador", "motivo": motivo},
        )

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
            # Verifica SuperUsuario para IDs fixos ou artistas após registro
            profile_info = self.repo.get_spotify_profile_temp()
            if profile_info:
                profile = {
                    "type": profile_info["type"],
                    "display_name": profile_info["display_name"],
                    "id": spotify_id,
                }
                self._verificar_e_criar_super_usuario(spotify_id, profile)
            self.repo.clear_temp()
            return {"success": True, "spotify_id": usuario.spotify_id}
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

            spotify_id = usuario.spotify_id
            spotify_token = usuario.spotify_token or ""

            # Refresh proativo do token Spotify se expirado
            # Isso evita o 401 na primeira chamada após login com email/senha
            token_renovado = False
            if spotify_token:
                try:
                    cfg = current_app.config
                    resp = requests.get(
                        f"{cfg['SPOTIFY_API_BASE']}/me",
                        headers={"Authorization": f"Bearer {spotify_token}"},
                        timeout=5,
                    )
                    if resp.status_code == 401 and usuario.spotify_refresh_token:
                        print(f"[login_with_password] Token Spotify expirado para {spotify_id}, tentando refresh...")
                        refresh_resp = requests.post(
                            cfg["SPOTIFY_TOKEN_URL"],
                            data={
                                "grant_type":    "refresh_token",
                                "refresh_token": usuario.spotify_refresh_token,
                                "client_id":     cfg["SPOTIFY_CLIENT_ID"],
                                "client_secret": cfg["SPOTIFY_CLIENT_SECRET"],
                            },
                            timeout=10,
                        )
                        if refresh_resp.ok:
                            tokens = refresh_resp.json()
                            new_token = tokens["access_token"]
                            new_refresh = tokens.get("refresh_token", usuario.spotify_refresh_token)
                            self.repo.update_user_spotify_tokens(spotify_id, new_token, new_refresh)
                            spotify_token = new_token
                            token_renovado = True
                            print(f"[login_with_password] Token Spotify renovado com sucesso para {spotify_id}")
                        else:
                            print(f"[login_with_password] Refresh falhou: {refresh_resp.status_code} {refresh_resp.text[:200]}")
                except requests.RequestException as e:
                    print(f"[login_with_password] Erro ao verificar/renovar token: {e}")

            # Garante que IDs fixos (SUPER_USER_IDS) tenham SuperUsuario/Moderador no banco
            # Isso é necessário porque o login por email/senha não passa pelo callback OAuth do Spotify
            is_fixed = spotify_id in current_app.config.get("SUPER_USER_IDS", [])
            if is_fixed:
                moderador = self.repo.get_moderador_by_usuario_id(spotify_id)
                if not moderador:
                    profile = {"type": "user", "display_name": email, "id": spotify_id}
                    self._verificar_e_criar_super_usuario(spotify_id, profile)
                    print(f"[INFO] SuperUsuario garantido no login-custom para ID fixo: {spotify_id}")

            return {"success": True, "spotify_id": spotify_id}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def set_user_password(self, usuario_id: str, password: str) -> dict:
        try:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            self.repo.update_user_password(usuario_id, password_hash)
            return {"success": True, "message": "Senha definida com sucesso!"}
        except Exception as e:
            return {"success": False, "message": str(e), "code": "password_update_error"}

    def send_reset_email(self, email: str) -> bool:
        """Gera um JWT de 1h e envia email com link de redefinição de senha.
        Retorna True mesmo se o email não existir no banco (não vaza informação)."""
        usuario = self.repo.get_usuario_by_email(email)
        if not usuario:
            # Não revela que o email não está cadastrado
            return True

        token = create_access_token(identity=email, expires_delta=timedelta(hours=1))
        frontend_url = current_app.config.get("FRONTEND_URL", "http://127.0.0.1:8080")
        reset_link = f"{frontend_url}/reset-password?token={token}"

        smtp_host = current_app.config.get("SMTP_HOST")
        if not smtp_host:
            # Dev mode: imprime o link no console em vez de enviar email
            print(f"[RESET PASSWORD] Link para {email}: {reset_link}")
            return True

        try:
            msg = MIMEText(
                f"Olá,\n\n"
                f"Você solicitou a redefinição de senha no MusicBot.\n\n"
                f"Clique no link abaixo para definir uma nova senha:\n"
                f"{reset_link}\n\n"
                f"Este link expira em 1 hora.\n\n"
                f"Se você não solicitou isso, ignore este email.\n",
                "plain",
                "utf-8",
            )
            msg["Subject"] = "MusicBot — Redefinição de Senha"
            msg["From"] = current_app.config["SMTP_FROM"]
            msg["To"] = email

            server = smtplib.SMTP(smtp_host, current_app.config["SMTP_PORT"])
            server.starttls()
            server.login(current_app.config["SMTP_USER"], current_app.config["SMTP_PASS"])
            server.sendmail(current_app.config["SMTP_FROM"], email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"[RESET PASSWORD] Erro ao enviar email: {e}")
            return False

    def reset_password(self, token: str, new_password: str) -> dict:
        """Valida o JWT de reset e atualiza a senha do usuário."""
        if len(new_password) < 6:
            return {"success": False, "message": "Senha deve ter no mínimo 6 caracteres", "code": "password_too_short"}

        try:
            decoded = decode_token(token)
            email = decoded.get("sub")
            if not email:
                return {"success": False, "message": "Token inválido", "code": "invalid_token"}

            password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            usuario = self.repo.get_usuario_by_email(email)
            if not usuario:
                return {"success": False, "message": "Usuário não encontrado", "code": "user_not_found"}

            self.repo.update_user_password(usuario.spotify_id, password_hash)
            return {"success": True, "message": "Senha redefinida com sucesso!"}
        except Exception:
            return {"success": False, "message": "Token inválido ou expirado", "code": "invalid_token"}

    def get_access_token(self) -> str | None:
        return self.repo.get_access_token_temp()
