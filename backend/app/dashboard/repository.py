from datetime import datetime, timezone, timedelta
from sqlalchemy import func, case
from app.database.connection import get_session
from app.database.models import (
    Chat, Pergunta, Resposta, Feedback, FeedbackTipo
)


class DashboardRepository:
    """Consultas ao banco de dados para a Dashboard."""

    def get_metricas(self, desde: datetime) -> dict:
        session = get_session()
        try:
            total_perguntas = (
                session.query(func.count(Pergunta.id))
                .join(Chat, Pergunta.chat_id == Chat.id)
                .filter(Pergunta.created_at >= desde)
                .scalar()
            ) or 0

            total_respostas = (
                session.query(func.count(Resposta.id))
                .join(Pergunta, Resposta.pergunta_id == Pergunta.id)
                .join(Chat, Pergunta.chat_id == Chat.id)
                .filter(Resposta.created_at >= desde)
                .scalar()
            ) or 0

            total_chats = (
                session.query(func.count(Chat.id))
                .filter(Chat.created_at >= desde)
                .scalar()
            ) or 0

            # Taxa de sucesso: respostas com pelo menos 1 like / total de respostas
            likes = (
                session.query(func.count(Feedback.id))
                .filter(
                    Feedback.tipo == FeedbackTipo.like,
                    Feedback.created_at >= desde,
                )
                .scalar()
            ) or 0

            dislikes = (
                session.query(func.count(Feedback.id))
                .filter(
                    Feedback.tipo == FeedbackTipo.dislike,
                    Feedback.created_at >= desde,
                )
                .scalar()
            ) or 0

            taxa_sucesso = (
                round(likes / (likes + dislikes) * 100, 1) if (likes + dislikes) > 0 else None
            )

            # Perguntas com reformulação: chats com mais de 1 pergunta (usuário reformulou)
            chats_com_multiplas_perguntas = (
                session.query(func.count())
                .select_from(
                    session.query(Pergunta.chat_id)
                    .filter(Pergunta.created_at >= desde)
                    .group_by(Pergunta.chat_id)
                    .having(func.count(Pergunta.id) > 1)
                    .subquery()
                )
                .scalar()
            ) or 0

            taxa_reformulacao = (
                round(chats_com_multiplas_perguntas / total_chats * 100, 1)
                if total_chats > 0
                else None
            )

            return {
                "total_perguntas": total_perguntas,
                "total_chats": total_chats,
                "taxa_sucesso": taxa_sucesso,
                "taxa_reformulacao": taxa_reformulacao,
                "total_likes": likes,
                "total_dislikes": dislikes,
            }
        finally:
            session.close()

    def get_perguntas_por_dia(self, desde: datetime) -> list[dict]:
        """Retorna contagem de perguntas agrupadas por dia."""
        session = get_session()
        try:
            rows = (
                session.query(
                    func.date(Pergunta.created_at).label("dia"),
                    func.count(Pergunta.id).label("total"),
                )
                .filter(Pergunta.created_at >= desde)
                .group_by(func.date(Pergunta.created_at))
                .order_by(func.date(Pergunta.created_at))
                .all()
            )
            return [{"dia": str(r.dia), "perguntas": r.total} for r in rows]
        finally:
            session.close()

    def get_feedbacks(self, desde: datetime, tipo: str | None = None) -> list[dict]:
        """Retorna likes e dislikes (avaliações). NÃO inclui reports."""
        session = get_session()
        try:
            q = (
                session.query(Feedback, Pergunta, Chat)
                .join(Resposta, Feedback.resposta_id == Resposta.id)
                .join(Pergunta, Resposta.pergunta_id == Pergunta.id)
                .join(Chat, Pergunta.chat_id == Chat.id)
                .filter(
                    Feedback.created_at >= desde,
                    Feedback.tipo.in_([FeedbackTipo.like, FeedbackTipo.dislike]),
                )
            )

            if tipo and tipo in ("like", "dislike"):
                q = q.filter(Feedback.tipo == FeedbackTipo[tipo])

            rows = q.order_by(Feedback.created_at.desc()).limit(100).all()

            return [
                {
                    "id": str(fb.id),
                    "tipo": fb.tipo.value,
                    "comentario": fb.comentario or "",
                    "conversa_titulo": chat.titulo,
                    "created_at": fb.created_at.isoformat(),
                }
                for fb, pergunta, chat in rows
            ]
        finally:
            session.close()

    def get_bugs(self, desde: datetime) -> list[dict]:
        """Retorna apenas reports (bugs). Likes/dislikes NÃO aparecem aqui."""
        session = get_session()
        try:
            rows = (
                session.query(Feedback)
                .filter(
                    Feedback.created_at >= desde,
                    Feedback.tipo == FeedbackTipo.report,
                )
                .order_by(Feedback.created_at.desc())
                .limit(100)
                .all()
            )

            return [
                {
                    "id": str(fb.id),
                    "comentario": fb.comentario or "",
                    "created_at": fb.created_at.isoformat(),
                }
                for fb in rows
            ]
        finally:
            session.close()

    def get_avaliacoes(self, desde: datetime, rating: str | None = None) -> list[dict]:
        """Retorna avaliações (like/dislike) recentes."""
        session = get_session()
        try:
            q = (
                session.query(Feedback)
                .filter(
                    Feedback.created_at >= desde,
                    Feedback.tipo.in_([FeedbackTipo.like, FeedbackTipo.dislike]),
                )
            )

            if rating == "positive":
                q = q.filter(Feedback.tipo == FeedbackTipo.like)
            elif rating == "negative":
                q = q.filter(Feedback.tipo == FeedbackTipo.dislike)

            rows = q.order_by(Feedback.created_at.desc()).limit(100).all()

            return [
                {
                    "id": str(fb.id),
                    "usuario_id": fb.usuario_id,
                    "avaliacao": "positive" if fb.tipo == FeedbackTipo.like else "negative",
                    "created_at": fb.created_at.isoformat(),
                }
                for fb in rows
            ]
        finally:
            session.close()
