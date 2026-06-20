from datetime import datetime, timezone, timedelta
from .repository import DashboardRepository


_PERIOD_DAYS = {
    "today": 1,
    "week": 7,
    "month": 30,
}


class DashboardService:
    def __init__(self):
        self._repo = DashboardRepository()

    def _desde(self, period: str) -> datetime:
        days = _PERIOD_DAYS.get(period, 7)
        return datetime.now(timezone.utc) - timedelta(days=days)

    def get_metricas(self, period: str) -> dict:
        return self._repo.get_metricas(self._desde(period))

    def get_grafico(self, period: str) -> list[dict]:
        return self._repo.get_perguntas_por_dia(self._desde(period))

    def get_feedbacks(self, period: str, tipo: str | None,
                      page: int = 1, per_page: int = 20) -> dict:
        return self._repo.get_feedbacks(self._desde(period), tipo, page, per_page)

    def get_avaliacoes(self, period: str, rating: str | None,
                       page: int = 1, per_page: int = 20) -> dict:
        return self._repo.get_avaliacoes(self._desde(period), rating, page, per_page)

    def get_bugs(self, period: str, page: int = 1, per_page: int = 20) -> dict:
        return self._repo.get_bugs(self._desde(period), page, per_page)
