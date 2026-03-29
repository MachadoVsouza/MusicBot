from flask_cors import CORS
from flask_session import Session

cors    = CORS()
session = Session()


def init_extensions(app):
    """Inicializa todas as extensões com a app factory."""
    session.init_app(app)
    cors.init_app(
        app,
        origins=[app.config["FRONTEND_URL"]],
        supports_credentials=True,
    )
