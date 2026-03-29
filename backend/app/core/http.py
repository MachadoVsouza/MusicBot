from flask import jsonify


def success(data: dict, status: int = 200):
    """Resposta de sucesso padronizada."""
    return jsonify(data), status


def error(message: str, status: int = 400, code: str = None):
    """Resposta de erro padronizada."""
    payload = {"error": code or message, "message": message}
    return jsonify(payload), status


def unauthorized(message: str = "Não autenticado"):
    return error(message, 401, "not_authenticated")


def not_found(message: str = "Recurso não encontrado"):
    return error(message, 404, "not_found")
