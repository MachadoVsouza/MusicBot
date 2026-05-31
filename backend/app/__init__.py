import os
from flask import Flask
from flask_jwt_extended import JWTManager
from .config import get_config
from .extensions import init_extensions
from .core.exceptions import AppError
from .core.http import error as http_error
from .rag.blueprint import rag_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())

    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-inseguro")
    JWTManager(app)

    init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    with app.app_context():
        from app.database.connection import init_db
        init_db()

    return app


def _register_blueprints(app: Flask) -> None:
    from .auth.blueprint      import auth_bp
    from .spotify.blueprint   import spotify_bp
    from .chat.blueprint      import chat_bp
    from .rag.blueprint       import rag_bp
    from .dashboard.blueprint import dashboard_bp

    app.register_blueprint(auth_bp)       # /auth/login, /auth/callback, /auth/logout
    app.register_blueprint(spotify_bp)    # /profile, /playlists, /recently-played ...
    app.register_blueprint(chat_bp)       # /chat/, /chat/<id>/message
    app.register_blueprint(rag_bp)        # /rag/, /rag/<id>/message
    app.register_blueprint(dashboard_bp)  # /dashboard/metrics, /chart, /feedbacks, /reviews


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