from flask import Flask
from .config import get_config
from .extensions import init_extensions
from .core.exceptions import AppError
from .core.http import error as http_error


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())

    init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    return app


def _register_blueprints(app: Flask) -> None:
    from .auth.blueprint    import auth_bp
    from .spotify.blueprint import spotify_bp

    app.register_blueprint(auth_bp)     # /auth/login, /auth/callback, /auth/logout
    app.register_blueprint(spotify_bp)  # /profile, /playlists, /recently-played ...


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(e: AppError):
        return http_error(e.message, e.status, e.code)

    @app.errorhandler(404)
    def handle_404(_):
        return http_error("Rota não encontrada", 404, "not_found")

    @app.errorhandler(500)
    def handle_500(_):
        return http_error("Erro interno do servidor", 500, "server_error")
