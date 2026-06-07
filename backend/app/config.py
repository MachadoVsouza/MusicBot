import os
class Config:
    # Flask
    SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-change-in-prod")

    # Flask-Session
    SESSION_TYPE            = "filesystem"
    SESSION_FILE_DIR        = "/tmp/flask_session"
    SESSION_PERMANENT       = False
    SESSION_USE_SIGNER      = True
    SESSION_COOKIE_SAMESITE = "Lax"     # Permite redirect GET cross-site (Spotify callback)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE   = False     # False em dev (HTTP), True em prod (HTTPS)
    SESSION_COOKIE_DOMAIN   = None

    # URLs
    FRONTEND_URL  = os.getenv("FRONTEND_URL",  "http://127.0.0.1:8080")
    REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/api/auth/callback")

    # Spotify
    # SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:5000/api/auth/callback")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "b5727e21ded847928278e6fe1782060f")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    SPOTIFY_AUTH_URL  = "https://accounts.spotify.com/authorize"
    SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
    SPOTIFY_API_BASE  = "https://api.spotify.com/v1"
    SPOTIFY_SCOPES = " ".join([
        "user-read-private",
        "user-read-email",
        "user-library-read",
        "user-top-read",
        "user-read-recently-played",
        "playlist-read-private",
        "playlist-modify-public",
        "playlist-modify-private",
        "user-modify-playback-state",
        "user-read-playback-state",
        "user-read-currently-playing",
    ])

    # ReccoBeats
    RECCO_API_BASE = "https://api.reccobeats.com/v1"
    RECCO_API_KEY  = os.getenv("RECCO_API_KEY", None)

    # Banco de dados
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://admin:admin@localhost:5432/MusicBot"
    )

    # IDs de usuários que são sempre SuperUsuários (moderadores fixos)
    SUPER_USER_IDS = [
        "818da73b30404df29b817237bd1a936c",
        "b5727e21ded847928278e6fe1782060f",
    ]

    # Provedor LLM ativo: "local" | "ifes"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")

    # Ollama — Local (para agente Spotify com latência baixa)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen:4b")
    OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30s")  # -1 = nunca descarrega

    # IFES Colatina — Workstations (para LLM e embeddings)
    IFES_BASE_URL = os.getenv("IFES_BASE_URL", "https://workstations.chatbotintegracar.online")
    IFES_API_KEY  = os.getenv("IFES_API_KEY", "")
    IFES_MODEL    = os.getenv("IFES_MODEL", "gemma3:12b")
    IFES_EMBEDDING_MODEL = os.getenv("IFES_EMBEDDING_MODEL", "nomic-embed-text")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_env = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
}

def get_config() -> type[Config]:
    env = os.getenv("FLASK_ENV", "development")
    return config_by_env.get(env, DevelopmentConfig)