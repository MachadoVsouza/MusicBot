import urllib.parse
from flask import Blueprint, redirect, request, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
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
    # Detecta URL base da request (funciona com tunnel/Cloudflare)
    forwarded_host = request.headers.get("X-Forwarded-Host")
    if forwarded_host:
        scheme = request.headers.get("X-Forwarded-Proto", "https")
        frontend = f"{scheme}://{forwarded_host.split(',')[0].strip()}"
    else:
        frontend = current_app.config["FRONTEND_URL"]
    svc      = _service()

    if request.args.get("error"):
        msg = urllib.parse.quote(request.args["error"])
        return redirect(f"{frontend}/entrar?error={msg}")

    if not svc.validate_state(request.args.get("state", "")):
        return redirect(f"{frontend}/entrar?error=state_invalido")

    if not svc.exchange_code(request.args.get("code", "")):
        return redirect(f"{frontend}/entrar?error=token_failed")

    result = svc.handle_spotify_callback()
    if not result.get("flow"):
        return redirect(f"{frontend}/entrar?error=profile_failed")

    flow = result["flow"]

    if flow == "login":
        jwt = create_access_token(identity=result["spotify_id"])
        token_enc = urllib.parse.quote(jwt)
        # Redireciona para /callback no frontend — que salva o token e vai para /chat
        return redirect(f"{frontend}/auth/callback?token={token_enc}")
    else:
        return redirect(f"{frontend}/registration-form")


@auth_bp.post("/register")
def register():
    svc  = _service()
    data = request.get_json(silent=True) or {}

    email    = (data.get("email") or "").strip()
    password = data.get("password", "")

    if not email:
        return error("Email é obrigatório", 400, "missing_email")
    if not password:
        return error("Senha é obrigatória", 400, "missing_password")
    if len(password) < 6:
        return error("Senha deve ter no mínimo 6 caracteres", 400, "password_too_short")

    result = svc.register_user(email=email, password=password)
    if not result.get("success"):
        return error(result.get("message", "Erro ao criar conta"), 400, result.get("code", "registration_failed"))

    jwt = create_access_token(identity=result["spotify_id"])
    return success({"token": jwt, "spotify_id": result["spotify_id"]}, 201)


@auth_bp.post("/login-custom")
def login_custom():
    svc  = _service()
    data = request.get_json(silent=True) or {}

    email    = (data.get("email") or "").strip()
    password = data.get("password", "")

    if not email or not password:
        return error("Email e senha são obrigatórios", 400, "missing_credentials")

    result = svc.login_with_password(email=email, password=password)
    if not result.get("success"):
        return unauthorized(result.get("message", "Credenciais inválidas"))

    jwt = create_access_token(identity=result["spotify_id"])
    return success({"token": jwt, "spotify_id": result["spotify_id"]})


@auth_bp.post("/set-password")
@jwt_required()
def set_password():
    usuario_id = get_jwt_identity()
    data       = request.get_json(silent=True) or {}
    password   = data.get("password", "")

    if not password:
        return error("Senha é obrigatória", 400, "missing_password")
    if len(password) < 6:
        return error("Senha deve ter no mínimo 6 caracteres", 400, "password_too_short")

    result = _service().set_user_password(usuario_id, password)
    if not result.get("success"):
        return error(result.get("message", "Erro ao definir senha"), 400, result.get("code"))

    return success({"message": result["message"]})


@auth_bp.post("/logout")
def logout():
    return "", 204


@auth_bp.get("/me")
@jwt_required()
def me():
    svc = _service()
    usuario_id = get_jwt_identity()
    moderador = svc.repo.get_moderador_by_usuario_id(usuario_id)

    role = "moderator" if moderador else "user"
    super_usuario_id = moderador.super_usuario_id if moderador else None

    super_ids = current_app.config.get("SUPER_USER_IDS", [])
    print(f"[DEBUG /me] usuario_id={usuario_id}, SUPER_USER_IDS={super_ids}, moderador={moderador is not None}, role={role}")

    # Fallback: IDs fixos sempre são moderadores
    if usuario_id in super_ids:
        print(f"[DEBUG /me] ID {usuario_id} encontrado em SUPER_USER_IDS, garantindo moderador...")
        role = "moderator"
        # Garante que o registro SuperUsuario/Moderador exista no banco
        if not moderador:
            moderador = svc.repo.garantir_super_usuario_para_id_fixo(usuario_id)
            if moderador:
                super_usuario_id = moderador.super_usuario_id
                print(f"[DEBUG /me] SuperUsuario criado via fallback: super_usuario_id={super_usuario_id}")

    result = {
        "usuario_id": usuario_id,
        "role": role,
        "super_usuario_id": super_usuario_id,
    }
    print(f"[DEBUG /me] Resposta: {result}")
    return success(result)
