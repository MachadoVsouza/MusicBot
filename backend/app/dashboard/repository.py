from datetime import datetime, timezone, timedelta
from sqlalchemy import func, case
from app.database.connection import get_session
from app.database.models import (
    Chat, Pergunta, Resposta, Feedback, FeedbackTipo, Usuario,
)
from sqlalchemy import desc, asc


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

    def get_feedbacks(self, desde: datetime, tipo: str | None = None,
                      page: int = 1, per_page: int = 20,
                      order_by: str = "created_at") -> dict:
        """Retorna likes e dislikes (avaliações) com paginação. NÃO inclui reports."""
        session = get_session()
        try:
            base = (
                session.query(Feedback, Usuario, Resposta, Chat)
                .join(Usuario, Feedback.usuario_id == Usuario.spotify_id)
                .join(Resposta, Feedback.resposta_id == Resposta.id)
                .join(Pergunta, Resposta.pergunta_id == Pergunta.id)
                .join(Chat, Pergunta.chat_id == Chat.id)
                .filter(
                    Feedback.created_at >= desde,
                    Feedback.tipo.in_([FeedbackTipo.like, FeedbackTipo.dislike]),
                )
            )

            if tipo and tipo in ("like", "dislike"):
                base = base.filter(Feedback.tipo == FeedbackTipo[tipo])

            total = base.count()
            offset = (page - 1) * per_page

            order_col = Feedback.id if order_by == "id" else Feedback.created_at
            order_dir = desc(order_col) if order_by == "created_at" else asc(order_col)

            rows = (
                base
                .order_by(order_dir)
                .offset(offset)
                .limit(per_page)
                .all()
            )

            items = [
                {
                    "id": str(fb.id),
                    "tipo": fb.tipo.value,
                    "usuario_email": usuario.email or usuario.spotify_id,
                    "conversa_titulo": chat.titulo,
                    "mensagem_avaliada": resposta.conteudo[:200] if resposta.conteudo else "",
                    "comentario": fb.comentario or "",
                    "created_at": fb.created_at.isoformat(),
                }
                for fb, usuario, resposta, chat in rows
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": max(1, (total + per_page - 1) // per_page),
            }
        finally:
            session.close()

    def get_bugs(self, desde: datetime, page: int = 1, per_page: int = 20) -> dict:
        """Retorna apenas reports (bugs) com paginação, incluindo usuário e conversa."""
        session = get_session()
        try:
            base = (
                session.query(Feedback, Usuario, Chat)
                .join(Usuario, Feedback.usuario_id == Usuario.spotify_id)
                .join(Resposta, Feedback.resposta_id == Resposta.id)
                .join(Pergunta, Resposta.pergunta_id == Pergunta.id)
                .join(Chat, Pergunta.chat_id == Chat.id)
                .filter(
                    Feedback.created_at >= desde,
                    Feedback.tipo == FeedbackTipo.report,
                )
            )

            total = base.count()
            offset = (page - 1) * per_page

            rows = (
                base
                .order_by(Feedback.created_at.desc())
                .offset(offset)
                .limit(per_page)
                .all()
            )

            items = [
                {
                    "id": str(fb.id),
                    "comentario": fb.comentario or "",
                    "usuario_email": usuario.email or usuario.spotify_id,
                    "conversa_titulo": chat.titulo,
                    "created_at": fb.created_at.isoformat(),
                }
                for fb, usuario, chat in rows
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": max(1, (total + per_page - 1) // per_page),
            }
        finally:
            session.close()

    def get_avaliacoes(self, desde: datetime, rating: str | None = None,
                       page: int = 1, per_page: int = 20) -> dict:
        """Retorna avaliações (like/dislike) recentes com paginação, incluindo usuário e conversa."""
        session = get_session()
        try:
            base = (
                session.query(Feedback, Usuario, Chat)
                .join(Usuario, Feedback.usuario_id == Usuario.spotify_id)
                .join(Resposta, Feedback.resposta_id == Resposta.id)
                .join(Pergunta, Resposta.pergunta_id == Pergunta.id)
                .join(Chat, Pergunta.chat_id == Chat.id)
                .filter(
                    Feedback.created_at >= desde,
                    Feedback.tipo.in_([FeedbackTipo.like, FeedbackTipo.dislike]),
                )
            )

            if rating == "positive":
                base = base.filter(Feedback.tipo == FeedbackTipo.like)
            elif rating == "negative":
                base = base.filter(Feedback.tipo == FeedbackTipo.dislike)

            total = base.count()
            offset = (page - 1) * per_page

            rows = (
                base
                .order_by(Feedback.created_at.desc())
                .offset(offset)
                .limit(per_page)
                .all()
            )

            items = [
                {
                    "id": str(fb.id),
                    "usuario_email": usuario.email or usuario.spotify_id,
                    "avaliacao": "positive" if fb.tipo == FeedbackTipo.like else "negative",
                    "comentario": fb.comentario or "",
                    "conversa_titulo": chat.titulo,
                    "created_at": fb.created_at.isoformat(),
                }
                for fb, usuario, chat in rows
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": max(1, (total + per_page - 1) // per_page),
            }
        finally:
            session.close()
