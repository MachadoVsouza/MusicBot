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
        
        print(f"[DEBUG] exchange_code: code={code[:20]}...")
        print(f"[DEBUG] SPOTIFY_TOKEN_URL={cfg['SPOTIFY_TOKEN_URL']}")
        print(f"[DEBUG] REDIRECT_URI={cfg['REDIRECT_URI']}")
        print(f"[DEBUG] SPOTIFY_CLIENT_ID={cfg['SPOTIFY_CLIENT_ID']}")
        print(f"[DEBUG] SPOTIFY_CLIENT_SECRET={'*' * 10 if cfg['SPOTIFY_CLIENT_SECRET'] else 'EMPTY'}")
        
        try:
            resp = requests.post(cfg["SPOTIFY_TOKEN_URL"], data={
                "grant_type":    "authorization_code",
                "code":          code,
                "redirect_uri":  cfg["REDIRECT_URI"],
                "client_id":     cfg["SPOTIFY_CLIENT_ID"],
                "client_secret": cfg["SPOTIFY_CLIENT_SECRET"],
                "code_verifier": self.repo.pop_verifier(),
            })

            print(f"[DEBUG] Spotify token response: status={resp.status_code}")
            
            if not resp.ok:
                print(f"[ERROR] Spotify token exchange failed: {resp.status_code} - {resp.text}")
                return False

            tokens = resp.json()
            self.repo.save_tokens(
                access_token  = tokens.get("access_token"),
                refresh_token = tokens.get("refresh_token"),
            )
            print("[SUCCESS] Tokens saved to session")
            return True
        except Exception as e:
            print(f"[ERROR] exchange_code exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def fetch_spotify_profile(self, access_token: str) -> dict | None:
        """Busca perfil do usuário no Spotify usando o access_token."""
        try:
            resp = requests.get(
                "https://api.spotify.com/v1/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if resp.ok:
                return resp.json()
        except Exception:
            pass
        return None

    def handle_spotify_callback(self) -> dict:
        """
        Após exchange_code, determina se é login (usuário existente) ou register (novo usuário).
        Retorna {"flow": "login" | "register", "spotify_id": str, "profile": dict}
        """
        access_token = self.repo.get_access_token()
        if not access_token:
            print("[ERROR] No access_token in session")
            return {"flow": None, "spotify_id": None, "profile": None}

        # Busca dados do Spotify
        profile = self.fetch_spotify_profile(access_token)
        if not profile:
            print("[ERROR] fetch_spotify_profile returned None")
            return {"flow": None, "spotify_id": None, "profile": None}

        spotify_id = profile.get("id")
        if not spotify_id:
            print("[ERROR] No spotify_id in profile")
            return {"flow": None, "spotify_id": None, "profile": None}

        print(f"[SUCCESS] Got spotify_id: {spotify_id}")
        # Armazena spotify_id na sessão
        self.repo.save_spotify_usuario_id(spotify_id)

        # Verifica se usuário já existe
        usuario = self.repo.get_usuario_by_spotify_id(spotify_id)
        
        if usuario:
            print(f"[SUCCESS] User exists: {usuario.id}")
            # Usuário existente: atualiza tokens e loga
            refresh_token = self.repo.get_refresh_token()
            self.repo.update_user_spotify_tokens(
                str(usuario.id), 
                spotify_id, 
                access_token, 
                refresh_token
            )
            self.repo.save_usuario_id(str(usuario.id))
            return {"flow": "login", "spotify_id": spotify_id, "profile": profile}
        else:
            print("[SUCCESS] New user, flow=register")
            # Novo usuário: apenas salva tokens, não cria usuario_id ainda
            # Salva refresh_token também para poder regar depois
            refresh_token = self.repo.get_refresh_token()
            self.repo.save_tokens(access_token, refresh_token)
            return {"flow": "register", "spotify_id": spotify_id, "profile": profile}

    def create_or_update_usuario(self) -> str | None:
        """
        Após exchange_code, busca perfil do Spotify e cria/atualiza usuário no banco.
        Retorna o usuario_id ou None se falhar.
        """
        access_token = self.repo.get_access_token()
        if not access_token:
            return None

        # Busca dados do Spotify
        profile = self.fetch_spotify_profile(access_token)
        if not profile:
            return None

        spotify_id = profile.get("id")
        email = profile.get("email", "")
        
        if not spotify_id:
            return None

        # Armazena spotify_id na sessão para ser usado em register_user() depois
        self.repo.save_spotify_usuario_id(spotify_id)

        # Cria/obtém usuário no banco
        usuario = self.repo.get_or_create_usuario_by_spotify(spotify_id, email)
        
        # Atualiza tokens do Spotify
        refresh_token = self.repo.get_refresh_token()
        self.repo.update_user_spotify_tokens(
            str(usuario.id), 
            spotify_id, 
            access_token, 
            refresh_token
        )
        
        # Armazena na sessão
        self.repo.save_usuario_id(str(usuario.id))
        
        return str(usuario.id)

    # ── Registration ──────────────────────────────────────────────────────────

    def register_user(self, email: str, password: str) -> dict:
        """
        Registra um novo usuário com dados customizados.
        
        Esperado que spotify_id e tokens já estejam na sessão.
        
        Returns:
        {
            "success": bool,
            "message": str,
            "code": str,
            "usuario_id": str (se sucesso)
        }
        """
        # Valida que tokens do Spotify existem
        spotify_id = self.repo.get_spotify_usuario_id()
        access_token = self.repo.get_access_token()
        refresh_token = self.repo.get_refresh_token()
        
        if not spotify_id or not access_token:
            return {
                "success": False,
                "message": "Tokens do Spotify não encontrados. Autentique novamente.",
                "code": "missing_spotify_tokens"
            }
        
        # Hash da senha
        try:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao processar senha: {str(e)}",
                "code": "password_hash_error"
            }
        
        # Cria/atualiza usuário no banco
        try:
            usuario = self.repo.create_user_with_password(
                email=email,
                password_hash=password_hash,
                spotify_id=spotify_id,
                spotify_token=access_token,
                spotify_refresh_token=refresh_token
            )
            
            # Armazena usuario_id na sessão (faz login automático)
            self.repo.save_usuario_id(str(usuario.id))
            
            return {
                "success": True,
                "message": "Usuário criado com sucesso!",
                "usuario_id": str(usuario.id)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao criar usuário: {str(e)}",
                "code": "user_creation_error"
            }

    def login_with_password(self, email: str, password: str) -> dict:
        """
        Autentica um usuário com email e senha.
        
        Returns:
        {
            "success": bool,
            "message": str,
            "usuario_id": str (se sucesso)
        }
        """
        from werkzeug.security import check_password_hash
        
        try:
            usuario = self.repo.get_usuario_by_email(email)
            
            if not usuario:
                return {
                    "success": False,
                    "message": "Email ou senha inválidos"
                }
            
            # Verifica se o usuário tem password_hash
            if not usuario.password_hash:
                return {
                    "success": False,
                    "message": "Esta conta não possui senha. Use Spotify para fazer login."
                }
            
            # Verifica a senha
            if not check_password_hash(usuario.password_hash, password):
                return {
                    "success": False,
                    "message": "Email ou senha inválidos"
                }
            
            # Salva usuario_id na sessão (faz login automático)
            self.repo.save_usuario_id(str(usuario.id))
            
            return {
                "success": True,
                "message": "Login realizado com sucesso!",
                "usuario_id": str(usuario.id)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao fazer login: {str(e)}"
            }

    def set_user_password(self, password: str) -> dict:
        """
        Define ou atualiza a senha de um usuário autenticado via Spotify.
        
        Returns:
        {
            "success": bool,
            "message": str,
            "code": str (se erro)
        }
        """
        from werkzeug.security import generate_password_hash
        
        try:
            # Obtém o usuario_id da sessão (deve estar autenticado)
            usuario_id = self.repo.get_usuario_id()
            
            if not usuario_id:
                return {
                    "success": False,
                    "message": "Usuário não autenticado",
                    "code": "not_authenticated"
                }
            
            # Hash da senha
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            
            # Atualiza a senha no banco
            self.repo.update_user_password(usuario_id, password_hash)
            
            return {
                "success": True,
                "message": "Senha definida com sucesso!"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao definir senha: {str(e)}",
                "code": "password_update_error"
            }

    # ── Session ───────────────────────────────────────────────────────────────

    def get_access_token(self) -> str | None:
        return self.repo.get_access_token()

    def get_usuario_id(self) -> str | None:
        return self.repo.get_usuario_id()

    def is_authenticated(self) -> bool:
        return self.repo.is_authenticated()

    def logout(self) -> None:
        self.repo.clear()
