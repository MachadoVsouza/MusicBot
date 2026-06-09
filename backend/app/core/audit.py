"""Registro de auditoria — log imutável de ações administrativas."""

import json
from flask import request
from app.database.connection import get_session
from app.database.models import AuditLog


def registrar_auditoria(usuario_id: str, acao: str, entidade: str,
                        entidade_id: int | None = None, detalhes: dict | None = None) -> None:
    """
    Registra uma ação administrativa no audit_log.

    Exemplos:
        registrar_auditoria("id123", "documento.aprovar", "documento", 5,
                            {"titulo": "História do Samba"})
        registrar_auditoria("id123", "moderador.criar", "moderador", None,
                            {"usuario_id": "id456", "nivel": "administrador"})
    """
    detalhes_str = json.dumps(detalhes, ensure_ascii=False) if detalhes else None

    log = AuditLog(
        usuario_id=usuario_id,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes_str,
        ip=request.remote_addr if request else None,
    )

    db = get_session()
    try:
        db.add(log)
        db.commit()
    finally:
        db.close()