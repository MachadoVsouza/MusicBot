import urllib.parse
from flask import Blueprint, redirect, request, current_app
from .service import AuthService
from .repository import AuthRepository
from app.core.http import success, unauthorized, error

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _service() -> AuthService:
    return AuthService(AuthRepository())


@auth_bp.get("/login")
def login():
    url = _service().build_auth_url()
    return redirect(url)


@auth_bp.get("/callback")
def callback():
    frontend = current_app.config["FRONTEND_URL"]
    svc      = _service()

    if request.args.get("error"):
        error_msg = urllib.parse.quote(request.args["error"])
        return redirect(f"{frontend}/entrar?error={error_msg}")

    if not svc.validate_state(request.args.get("state", "")):
        return redirect(f"{frontend}/entrar?error=state_invalido")

    code = request.args.get("code", "")
    if not svc.exchange_code(code):
        return redirect(f"{frontend}/entrar?error=token_failed")

    result = svc.handle_spotify_callback()
    
    if not result.get("flow"):
        return redirect(f"{frontend}/entrar?error=profile_failed")
    
    flow = result["flow"]
    
    if flow == "login":
        return redirect(f"{frontend}/chat")
    else:
        return redirect(f"{frontend}/registration-form")


@auth_bp.post("/register")
def register():
    svc = _service()
    
    if not svc.get_access_token():
        return error("Você precisa autenticar com Spotify primeiro", 401, "missing_spotify_auth")
    
    data = request.get_json(silent=True) or {}
    
    email = (data.get("email") or "").strip()
    password = data.get("password", "")
    
    if not email:
        return error("Email é obrigatório", 400, "missing_email")
    if not password:
        return error("Senha é obrigatória", 400, "missing_password")
    if len(password) < 6:
        return error("Senha deve ter no mínimo 6 caracteres", 400, "password_too_short")
    
    result = svc.register_user(email=email, password=password)
    
    if not result.get("success"):
        return error(
            result.get("message", "Erro ao criar conta"),
            400,
            result.get("code", "registration_failed")
        )
    
    return success({
        "message": "Conta criada com sucesso!",
        "usuario_id": result.get("usuario_id"),
    }, 201)


@auth_bp.post("/login-custom")
def login_custom():
    svc = _service()
    data = request.get_json(silent=True) or {}
    
    email = (data.get("email") or "").strip()
    password = data.get("password", "")
    
    if not email or not password:
        return error("Email e senha são obrigatórios", 400, "missing_credentials")
    
    result = svc.login_with_password(email=email, password=password)
    
    if not result.get("success"):
        return unauthorized(result.get("message", "Credenciais inválidas"))
    
    return success({
        "message": "Login realizado com sucesso!",
        "usuario_id": result.get("usuario_id"),
    })


@auth_bp.post("/set-password")
def set_password():
    svc = _service()
    
    if not svc.get_access_token():
        return error("Você precisa autenticar com Spotify primeiro", 401, "missing_spotify_auth")
    
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    
    if not password:
        return error("Senha é obrigatória", 400, "missing_password")
    if len(password) < 6:
        return error("Senha deve ter no mínimo 6 caracteres", 400, "password_too_short")
    
    result = svc.set_user_password(password=password)
    
    if not result.get("success"):
        return error(
            result.get("message", "Erro ao definir senha"),
            400,
            result.get("code", "set_password_failed")
        )
    
    return success({
        "message": result.get("message", "Senha definida com sucesso!"),
    })


@auth_bp.get("/logout")
def logout():
    _service().logout()
    return "", 204
