import urllib.parse
from flask import Blueprint, redirect, request, current_app
from .service import AuthService
from .repository import AuthRepository
from app.core.http import success, unauthorized

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
        error = urllib.parse.quote(request.args["error"])
        return redirect(f"{frontend}/entrar?error={error}")

    if not svc.validate_state(request.args.get("state", "")):
        return redirect(f"{frontend}/entrar?error=state_invalido")

    code = request.args.get("code", "")
    if not svc.exchange_code(code):
        return redirect(f"{frontend}/entrar?error=token_failed")

    return redirect(f"{frontend}/profile")


@auth_bp.get("/logout")
def logout():
    _service().logout()
    return "", 204


# ── Debug (remover em produção) ───────────────────────────────────────────────

@auth_bp.get("/debug")
def debug():
    from flask import session
    return success({
        "cookies":         dict(request.cookies),
        "session_keys":    list(session.keys()),
        "authenticated":   _service().is_authenticated(),
    })
