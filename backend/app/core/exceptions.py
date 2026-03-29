class AppError(Exception):
    """Base para todos os erros da aplicação."""
    def __init__(self, message: str, status: int = 400, code: str = None):
        super().__init__(message)
        self.message = message
        self.status  = status
        self.code    = code or "app_error"


class AuthError(AppError):
    def __init__(self, message: str = "Não autenticado"):
        super().__init__(message, 401, "not_authenticated")


class SpotifyError(AppError):
    def __init__(self, message: str = "Erro ao comunicar com o Spotify"):
        super().__init__(message, 502, "spotify_error")


class NotFoundError(AppError):
    def __init__(self, message: str = "Recurso não encontrado"):
        super().__init__(message, 404, "not_found")
