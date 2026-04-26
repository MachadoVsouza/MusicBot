from datetime import datetime, timezone
from app.database.connection import get_session
from app.database.models import Documento, Fragmento, RespostaFonte, DocumentoStatus
from .client import get_embedding

SIMILARITY_THRESHOLD = 0.15  # distância coseno — abaixo disso considera duplicata


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
        """Salva o documento com status PENDENTE — aguarda aprovação do moderador."""
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
        """Marca o documento como aprovado e registra quem aprovou e quando."""
        db = get_session()
        try:
            doc = db.get(Documento, documento_id)
            if not doc:
                return None
            doc.status      = DocumentoStatus.aprovado
            doc.aprovado_por = aprovado_por
            doc.aprovado_em  = datetime.now(timezone.utc)
            db.commit()
            db.refresh(doc)
            return doc
        finally:
            db.close()

    def rejeitar_documento(self, documento_id: int, aprovado_por: str, motivo: str) -> Documento | None:
        """Marca o documento como rejeitado, registra quem rejeitou e o motivo."""
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
        """
        Verifica se já existe conteúdo similar na base.
        Retorna True se for duplicata (distância coseno abaixo do threshold).
        """
        embedding = get_embedding(conteudo)
        if not embedding:
            return False

        db = get_session()
        try:
            similar = (
                db.query(Fragmento)
                .filter(Fragmento.embedding.isnot(None))
                .order_by(Fragmento.embedding.cosine_distance(embedding))
                .first()
            )
            if not similar:
                return False

            distancia = similar.embedding.cosine_distance(embedding)
            return distancia < SIMILARITY_THRESHOLD
        finally:
            db.close()

    def salvar_fragmento(self, documento_id: int, conteudo: str) -> Fragmento | None:
        """Gera o embedding do chunk e salva no banco."""
        embedding = get_embedding(conteudo)
        if not embedding:
            return None

        db = get_session()
        try:
            fragmento = Fragmento(
                documento_id = documento_id,
                conteudo     = conteudo,
                embedding    = embedding,
            )
            db.add(fragmento)
            db.commit()
            db.refresh(fragmento)
            return fragmento
        finally:
            db.close()

    def buscar_similares(self, pergunta: str, limite: int = 3) -> list[Fragmento]:
        """Busca fragmentos mais similares usando distância coseno."""
        embedding = get_embedding(pergunta)
        if not embedding:
            return []

        db = get_session()
        try:
            return (
                db.query(Fragmento)
                .join(Documento)
                .filter(
                    Fragmento.embedding.isnot(None),
                    Documento.status == DocumentoStatus.aprovado,
                    Documento.ativo  == True,
                )
                .order_by(Fragmento.embedding.cosine_distance(embedding))
                .limit(limite)
                .all()
            )
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
