from flask import Blueprint, request
from .service import DashboardService
from app.core.auth_guard import require_auth
from app.core.http import success

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _svc() -> DashboardService:
    return DashboardService()


@dashboard_bp.get("/metrics")
@require_auth
def get_metrics(token: str, usuario_id: str):
    period = request.args.get("period", "week")
    return success(_svc().get_metricas(period))


@dashboard_bp.get("/chart")
@require_auth
def get_chart(token: str, usuario_id: str):
    period = request.args.get("period", "week")
    return success({"data": _svc().get_grafico(period)})


@dashboard_bp.get("/feedbacks")
@require_auth
def get_feedbacks(token: str, usuario_id: str):
    period = request.args.get("period", "week")
    tipo   = request.args.get("tipo") or None
    return success({"feedbacks": _svc().get_feedbacks(period, tipo)})


@dashboard_bp.get("/reviews")
@require_auth
def get_reviews(token: str, usuario_id: str):
    period = request.args.get("period", "week")
    rating = request.args.get("rating") or None
    return success({"reviews": _svc().get_avaliacoes(period, rating)})
