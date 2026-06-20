from datetime import datetime, timezone

from flask import Blueprint, request, Response
from .service import DashboardService
from app.core.auth_guard import require_moderator
from app.core.http import success

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _svc() -> DashboardService:
    return DashboardService()


@dashboard_bp.get("/metrics")
@require_moderator
def get_metrics(token: str, usuario_id: str):
    period = request.args.get("period", "week")
    return success(_svc().get_metricas(period))


@dashboard_bp.get("/chart")
@require_moderator
def get_chart(token: str, usuario_id: str):
    period = request.args.get("period", "week")
    return success({"data": _svc().get_grafico(period)})


@dashboard_bp.get("/feedbacks")
@require_moderator
def get_feedbacks(token: str, usuario_id: str):
    """Retorna likes e dislikes (avaliações) com paginação. NÃO inclui reports."""
    period   = request.args.get("period", "week")
    tipo     = request.args.get("tipo") or None
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    return success(_svc().get_feedbacks(period, tipo, page, per_page))


@dashboard_bp.get("/reviews")
@require_moderator
def get_reviews(token: str, usuario_id: str):
    """Retorna avaliações (likes/dislikes) consolidadas com paginação."""
    period   = request.args.get("period", "week")
    rating   = request.args.get("rating") or None
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    return success(_svc().get_avaliacoes(period, rating, page, per_page))


@dashboard_bp.get("/bugs")
@require_moderator
def get_bugs(token: str, usuario_id: str):
    """Retorna apenas reports (bugs) com paginação. Likes/dislikes NÃO aparecem aqui."""
    period   = request.args.get("period", "week")
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    return success(_svc().get_bugs(period, page, per_page))


@dashboard_bp.get("/export")
@require_moderator
def exportar_relatorio(token: str, usuario_id: str):
    """
    Exporta o relatório do dashboard em PDF.
    ?period=today|week|month (padrão: week)
    """
    period = request.args.get("period", "week")
    fmt = request.args.get("format", "pdf").lower()

    metricas = _svc().get_metricas(period)
    grafico = _svc().get_grafico(period)

    if fmt == "csv":
        import csv
        import io as csv_io
        buf = csv_io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Métrica", "Valor"])
        writer.writerow(["Total de Perguntas", metricas.get("total_perguntas", 0)])
        writer.writerow(["Total de Conversas", metricas.get("total_chats", 0)])
        writer.writerow(["Taxa de Sucesso (%)", metricas.get("taxa_sucesso", 0)])
        writer.writerow(["Taxa de Reformulação (%)", metricas.get("taxa_reformulacao", 0)])
        writer.writerow(["Total de Likes", metricas.get("total_likes", 0)])
        writer.writerow(["Total de Dislikes", metricas.get("total_dislikes", 0)])
        if grafico:
            writer.writerow([])
            writer.writerow(["Dia", "Perguntas"])
            for g in grafico:
                writer.writerow([g["dia"], g["perguntas"]])
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=relatorio_dashboard_{period}.csv"},
        )

    if fmt == "json":
        import json
        content = json.dumps({
            "period": period,
            "metricas": metricas,
            "grafico": grafico,
            "gerado_em": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2)
        return Response(
            content,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename=relatorio_dashboard_{period}.json"},
        )

    # PDF
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    import io
    from datetime import datetime, timezone

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title2', parent=styles['Heading1'], fontSize=18, spaceAfter=12, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('SubTitle2', parent=styles['Normal'], fontSize=10, textColor='#666666', alignment=TA_CENTER)

    elements = []
    elements.append(Paragraph("Relatório do MusicBot", title_style))
    elements.append(Paragraph(f"Período: {period} | Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))

    # Métricas
    elements.append(Paragraph("<b>Métricas</b>", styles['Heading2']))
    metric_data = [
        ["Métrica", "Valor"],
        ["Total de Perguntas", str(metricas.get("total_perguntas", 0))],
        ["Total de Conversas", str(metricas.get("total_chats", 0))],
        ["Taxa de Sucesso", f"{metricas.get('taxa_sucesso', 0)}%"],
        ["Taxa de Reformulação", f"{metricas.get('taxa_reformulacao', 0)}%"],
        ["Total de Likes", str(metricas.get("total_likes", 0))],
        ["Total de Dislikes", str(metricas.get("total_dislikes", 0))],
    ]
    table = Table(metric_data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#1DB954'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#FFFFFF'),
        ('GRID', (0, 0), (-1, -1), 0.5, '#CCCCCC'),
        ('BACKGROUND', (0, 1), (-1, -1), '#F5F5F5'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))

    # Gráfico (tabela de perguntas por dia)
    if grafico:
        elements.append(Paragraph("<b>Perguntas por Dia</b>", styles['Heading2']))
        chart_data = [["Dia", "Perguntas"]] + [[g["dia"], str(g["perguntas"])] for g in grafico]
        chart_table = Table(chart_data, colWidths=[3*inch, 2*inch])
        chart_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#282828'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#FFFFFF'),
            ('GRID', (0, 0), (-1, -1), 0.5, '#CCCCCC'),
        ]))
        elements.append(chart_table)

    doc.build(elements)
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_dashboard_{period}.pdf"},
    )
