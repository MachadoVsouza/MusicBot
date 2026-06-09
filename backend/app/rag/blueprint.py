from datetime import datetime, timezone

from flask import Blueprint, request, Response
from .service import RagService
from app.core.auth_guard import require_auth
from app.core.http import success, error, not_found
from app.core.audit import registrar_auditoria
from app.spotify.repository import SpotifyRepository
from app.spotify.service import SpotifyService
from app.database.connection import get_session
from app.database.models import AuditLog

rag_bp = Blueprint("rag", __name__, url_prefix="/rag")


def _svc() -> RagService:
    return RagService()


def _get_spotify_id(token: str) -> str:
    return SpotifyService(SpotifyRepository(token)).get_profile()["id"]


@rag_bp.post("/documentos")
@require_auth
def submeter_documento(token: str, usuario_id: str):
    spotify_id = _get_spotify_id(token)

    if request.files.get("arquivo"):
        arquivo          = request.files["arquivo"]
        titulo           = request.form.get("titulo", arquivo.filename)
        super_usuario_id = request.form.get("super_usuario_id")
        if not super_usuario_id:
            return error("Campo 'super_usuario_id' obrigatório", 400)
        resultado = _svc().submeter_documento(
            super_usuario_id=int(super_usuario_id),
            titulo=titulo,
            conteudo="",
            tipo="pdf",
            uploaded_by=spotify_id,
            pdf_bytes=arquivo.read(),
        )
    else:
        body             = request.get_json(silent=True) or {}
        titulo           = body.get("titulo", "").strip()
        tipo             = body.get("tipo", "txt")
        super_usuario_id = body.get("super_usuario_id")
        conteudo         = body.get("conteudo", "").strip()
        url              = body.get("url", "").strip()

        if not titulo:
            return error("Campo 'titulo' obrigatório", 400)
        if not super_usuario_id:
            return error("Campo 'super_usuario_id' obrigatório", 400)
        if tipo == "link" and not url:
            return error("Campo 'url' obrigatório para tipo link", 400)
        if tipo == "txt" and not conteudo:
            return error("Campo 'conteudo' obrigatório para tipo txt", 400)

        resultado = _svc().submeter_documento(
            super_usuario_id=super_usuario_id,
            titulo=titulo,
            conteudo=conteudo,
            tipo=tipo,
            uploaded_by=spotify_id,
            url=url if tipo == "link" else None,
        )

    if "erro" in resultado:
        return error(resultado["erro"], 422)
    if resultado.get("duplicata"):
        return success(resultado, 200)
    return success(resultado, 201)


@rag_bp.get("/documentos")
@require_auth
def listar_documentos(token: str, usuario_id: str):
    status = request.args.get("status")
    documentos = _svc().listar_documentos(status)

    # Enriquece cada documento com o nome do super_usuario (para exibição em vez do ID)
    result = []
    for doc in documentos:
        nome = None
        if doc.get("super_usuario_id"):
            db = get_session()
            try:
                from app.database.models import SuperUsuario
                su = db.get(SuperUsuario, doc["super_usuario_id"])
                if su:
                    nome = su.nome
            finally:
                db.close()
        result.append({**doc, "super_usuario_nome": nome})

    return success({"documentos": result})


@rag_bp.post("/documentos/<int:documento_id>/aprovar")
@require_auth
def aprovar_documento(token: str, usuario_id: str, documento_id: int):
    spotify_id = _get_spotify_id(token)
    resultado  = _svc().aprovar_e_indexar(documento_id, spotify_id)
    if "erro" in resultado:
        return not_found(resultado["erro"])
    registrar_auditoria(
        usuario_id=spotify_id,
        acao="documento.aprovar",
        entidade="documento",
        entidade_id=documento_id,
        detalhes={"documento_id": documento_id},
    )
    return success(resultado)


@rag_bp.post("/documentos/<int:documento_id>/rejeitar")
@require_auth
def rejeitar_documento(token: str, usuario_id: str, documento_id: int):
    body   = request.get_json(silent=True) or {}
    motivo = body.get("motivo", "").strip()
    if not motivo:
        return error("Campo 'motivo' obrigatório", 400)
    spotify_id = _get_spotify_id(token)
    resultado  = _svc().rejeitar_documento(documento_id, spotify_id, motivo)
    if "erro" in resultado:
        return not_found(resultado["erro"])
    registrar_auditoria(
        usuario_id=spotify_id,
        acao="documento.rejeitar",
        entidade="documento",
        entidade_id=documento_id,
        detalhes={"documento_id": documento_id, "motivo": motivo},
    )
    return success(resultado)


@rag_bp.delete("/documentos/<int:documento_id>")
@require_auth
def deletar_documento(token: str, usuario_id: str, documento_id: int):
    spotify_id = _get_spotify_id(token)
    ok = _svc().deletar_documento(documento_id)
    if not ok:
        return not_found("Documento não encontrado")
    registrar_auditoria(
        usuario_id=spotify_id,
        acao="documento.excluir",
        entidade="documento",
        entidade_id=documento_id,
        detalhes={"documento_id": documento_id},
    )
    return success({"ok": True})


@rag_bp.get("/buscar")
@require_auth
def buscar(token: str, usuario_id: str):
    pergunta = request.args.get("q", "").strip()
    if not pergunta:
        return error("Parâmetro 'q' obrigatório", 400)
    return success({"resultados": _svc().buscar_contexto(pergunta)})


@rag_bp.get("/auditoria/export")
@require_auth
def exportar_auditoria(token: str, usuario_id: str):
    """
    Exporta o relatório de auditoria (audit_log) em PDF ou CSV.
    ?format=pdf|csv (padrão: pdf)
    """
    fmt = request.args.get("format", "pdf").lower()

    # Mapeamento de ações para labels legíveis
    ACAO_LABELS = {
        "documento.aprovar": "Aceito",
        "documento.rejeitar": "Rejeitado",
        "documento.excluir": "Excluído",
        "moderador.criar_automatico": "Criado automaticamente",
    }

    db = get_session()
    try:
        from app.database.models import SuperUsuario, Documento, Moderador
        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(500)
            .all()
        )

        # Resolve nomes de usuários e títulos de documentos em lote
        user_ids = list({log.usuario_id for log in logs if log.usuario_id})
        doc_ids = list({log.entidade_id for log in logs if log.entidade == "documento" and log.entidade_id})

        # Nome do usuário via Moderador → SuperUsuario
        nome_map = {}
        if user_ids:
            mods = db.query(Moderador).filter(Moderador.usuario_id.in_(user_ids)).all()
            su_ids = {m.super_usuario_id for m in mods}
            sus = db.query(SuperUsuario).filter(SuperUsuario.id.in_(su_ids)).all() if su_ids else []
            su_by_id = {su.id: su for su in sus}
            for m in mods:
                su = su_by_id.get(m.super_usuario_id)
                if su:
                    nome_map[m.usuario_id] = su.nome

        doc_map = {}
        if doc_ids:
            docs = db.query(Documento).filter(Documento.id.in_(doc_ids)).all()
            doc_map = {d.id: d.titulo for d in docs}
    finally:
        db.close()

    # Constrói linhas enriquecidas
    linhas = []
    for log in logs:
        nome = nome_map.get(log.usuario_id)
        nome_usuario = nome if nome else (log.usuario_id[:12] + "..." if len(log.usuario_id) > 12 else log.usuario_id)
        acao_label = ACAO_LABELS.get(log.acao, log.acao)
        titulo_doc = doc_map.get(log.entidade_id, f"Doc #{log.entidade_id}") if log.entidade == "documento" and log.entidade_id else log.entidade
        data_str = log.created_at.strftime("%d/%m/%Y %H:%M") if log.created_at else ""
        linhas.append({
            "id": log.id,
            "usuario": nome_usuario,
            "acao": acao_label,
            "entidade": titulo_doc,
            "data": data_str,
        })

    if fmt == "csv":
        import csv
        import io as csv_io
        buf = csv_io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["ID", "Usuário", "Ação", "Entidade", "Data"])
        for l in linhas:
            writer.writerow([l["id"], l["usuario"], l["acao"], l["entidade"], l["data"]])
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=auditoria_base_conhecimento.csv"},
        )

    # PDF
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title2', parent=styles['Heading1'], fontSize=18, spaceAfter=12, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('SubTitle2', parent=styles['Normal'], fontSize=10, textColor='#666666', alignment=TA_CENTER)

    elements = []
    elements.append(Paragraph("Relatório de Auditoria — Base de Conhecimento", title_style))
    elements.append(Paragraph(f"Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} | Registros: {len(linhas)}", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))

    table_data = [["ID", "Usuário", "Ação", "Entidade (Documento)", "Data"]]
    for l in linhas:
        table_data.append([str(l["id"]), l["usuario"], l["acao"], l["entidade"], l["data"]])

    col_widths = [0.4*inch, 1.3*inch, 1.2*inch, 2.0*inch, 1.2*inch]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#1DB954'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#FFFFFF'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, '#CCCCCC'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), ['#F5F5F5', '#FFFFFF']),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=auditoria_base_conhecimento.pdf"},
    )
