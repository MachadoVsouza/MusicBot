import logging
from datetime import datetime, timezone
from app.database.connection import get_session
from app.database.models import Documento, Fragmento, RespostaFonte, DocumentoStatus
from .client import get_embedding, get_embeddings_batch

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.15


class RagRepository:

    # ── Documento ─────────────────────────────────────────────────────────────

    def salvar_documento_pendente(
        self,
        super_usuario_id: int,
        titulo: str,
        conteudo: str,
        tipo: str,
        uploaded_by: str,
    ) -> Documento:
        db = get_session()
        try:
            doc = Documento(
                super_usuario_id  = super_usuario_id,
                titulo            = titulo,
                conteudo_original = conteudo,
                tipo              = tipo,
                uploaded_by       = uploaded_by,
                status            = DocumentoStatus.pendente,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return doc
        finally:
            db.close()

    def aprovar_documento(self, documento_id: int, aprovado_por: str) -> Documento | None:
        db = get_session()
        try:
            doc = db.get(Documento, documento_id)
            if not doc:
                return None
            doc.status       = DocumentoStatus.aprovado
            doc.aprovado_por = aprovado_por
            doc.aprovado_em  = datetime.now(timezone.utc)
            db.commit()
            db.refresh(doc)
            return doc
        finally:
            db.close()

    def rejeitar_documento(self, documento_id: int, aprovado_por: str, motivo: str) -> Documento | None:
        db = get_session()
        try:
            doc = db.get(Documento, documento_id)
            if not doc:
                return None
            doc.status          = DocumentoStatus.rejeitado
            doc.aprovado_por    = aprovado_por
            doc.aprovado_em     = datetime.now(timezone.utc)
            doc.motivo_rejeicao = motivo
            db.commit()
            db.refresh(doc)
            return doc
        finally:
            db.close()

    def listar_documentos(self, status: DocumentoStatus = None) -> list[Documento]:
        db = get_session()
        try:
            query = db.query(Documento).filter(Documento.ativo == True)
            if status:
                query = query.filter(Documento.status == status)
            return query.order_by(Documento.uploaded_at.desc()).all()
        finally:
            db.close()

    def deletar_documento(self, documento_id: int) -> bool:
        db = get_session()
        try:
            doc = db.get(Documento, documento_id)
            if not doc:
                return False
            doc.ativo = False
            db.commit()
            return True
        finally:
            db.close()

    # ── Fragmento ─────────────────────────────────────────────────────────────

    def verificar_duplicata(self, conteudo: str) -> bool:
        embedding = get_embedding(conteudo)
        if not embedding:
            return False
        db = get_session()
        try:
            from sqlalchemy import text
            result = db.execute(
                text("""
                    SELECT embedding <=> :emb AS distancia
                    FROM fragmento
                    WHERE embedding IS NOT NULL
                    ORDER BY distancia
                    LIMIT 1
                """),
                {"emb": str(embedding)}
            ).first()
            return bool(result and result.distancia < SIMILARITY_THRESHOLD)
        finally:
            db.close()

    def salvar_fragmentos_batch(self, documento_id: int, chunks: list[str]) -> tuple[int, int]:
        """Salva múltiplos chunks em batch — muito mais eficiente que um por um."""
        embeddings = get_embeddings_batch(chunks)
        if not embeddings:
            return 0, len(chunks)

        db = get_session()
        indexados = 0
        falhos    = 0
        try:
            for chunk, embedding in zip(chunks, embeddings):
                try:
                    db.add(Fragmento(
                        documento_id = documento_id,
                        conteudo     = chunk,
                        embedding    = embedding,
                    ))
                    indexados += 1
                except Exception:
                    logger.exception("Erro ao salvar fragmento")
                    falhos += 1
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Erro no batch de fragmentos")
        finally:
            db.close()
        return indexados, falhos

    def buscar_similares(self, pergunta: str, limite: int = 5) -> list[Fragmento]:
        embedding = get_embedding(pergunta)
        if not embedding:
            return []
        db = get_session()
        try:
            from sqlalchemy import text
            rows = db.execute(
                text("""
                    SELECT f.id, f.embedding <=> :emb AS distancia
                    FROM fragmento f
                    JOIN documento d ON d.id = f.documento_id
                    WHERE f.embedding IS NOT NULL
                      AND d.status = 'aprovado'
                      AND d.ativo  = TRUE
                    ORDER BY distancia
                    LIMIT :limite
                """),
                {"emb": str(embedding), "limite": limite}
            ).fetchall()

            ids = [r.id for r in rows]
            if not ids:
                return []

            fragmentos = db.query(Fragmento).filter(Fragmento.id.in_(ids)).all()
            # Reordena pelo ranking original da busca vetorial
            ordem = {fid: i for i, fid in enumerate(ids)}
            return sorted(fragmentos, key=lambda f: ordem.get(f.id, 999))
        finally:
            db.close()

    def salvar_fontes(self, resposta_id: int, fragmento_ids: list[int]) -> None:
        db = get_session()
        try:
            for fid in fragmento_ids:
                db.add(RespostaFonte(resposta_id=resposta_id, fragmento_id=fid))
            db.commit()
        finally:
            db.close()