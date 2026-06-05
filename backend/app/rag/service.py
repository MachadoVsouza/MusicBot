import re
import logging
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .repository import RagRepository

logger = logging.getLogger(__name__)

_splitter = RecursiveCharacterTextSplitter(
    chunk_size         = 600,
    chunk_overlap      = 100,
    separators         = ["\n\n", "\n", ". ", " ", ""],
    length_function    = len,
)


class RagService:
    def __init__(self):
        self.repo = RagRepository()

    # ── Extração ──────────────────────────────────────────────────────────────

    def _extrair_de_url(self, url: str) -> str | None:
        try:
            resp  = requests.get(url, timeout=15)
            resp.raise_for_status()
            texto = re.sub(r'<[^>]+>', ' ', resp.text)
            texto = re.sub(r'\s+', ' ', texto).strip()
            return texto[:50000]
        except Exception:
            logger.exception("Erro ao extrair URL: %s", url)
            return None

    def _extrair_de_pdf(self, conteudo_bytes: bytes) -> str | None:
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(conteudo_bytes))
            return "\n".join(p.extract_text() or "" for p in reader.pages).strip()
        except Exception:
            logger.exception("Erro ao extrair PDF")
            return None

    # ── Chunking via LangChain ────────────────────────────────────────────────

    def _chunk_text(self, texto: str) -> list[str]:
        chunks = _splitter.split_text(texto)
        return [c.strip() for c in chunks if len(c.strip()) > 30]

    # ── Upload ────────────────────────────────────────────────────────────────

    def submeter_documento(
        self,
        super_usuario_id: int,
        titulo: str,
        conteudo: str,
        tipo: str,
        uploaded_by: str,
        url: str = None,
        pdf_bytes: bytes = None,
    ) -> dict:
        if tipo == "link" and url:
            conteudo = self._extrair_de_url(url)
            if not conteudo:
                return {"erro": "Não foi possível extrair conteúdo da URL."}
        elif tipo == "pdf" and pdf_bytes:
            conteudo = self._extrair_de_pdf(pdf_bytes)
            if not conteudo:
                return {"erro": "Não foi possível extrair texto do PDF."}

        if self.repo.verificar_duplicata(conteudo[:500]):
            return {"duplicata": True, "mensagem": "Já existe conteúdo similar na base de conhecimento."}

        doc = self.repo.salvar_documento_pendente(
            super_usuario_id = super_usuario_id,
            titulo           = titulo,
            conteudo         = conteudo,
            tipo             = tipo,
            uploaded_by      = uploaded_by,
        )
        return {
            "documento_id": doc.id,
            "titulo":       doc.titulo,
            "status":       doc.status.value,
            "mensagem":     "Documento enviado e aguardando aprovação do moderador.",
        }

    # ── Aprovação ─────────────────────────────────────────────────────────────

    def aprovar_e_indexar(self, documento_id: int, aprovado_por: str) -> dict:
        doc = self.repo.aprovar_documento(documento_id, aprovado_por)
        if not doc:
            return {"erro": "Documento não encontrado."}

        chunks              = self._chunk_text(doc.conteudo_original)
        indexados, falhos   = self.repo.salvar_fragmentos_batch(documento_id, chunks)

        return {
            "documento_id": doc.id,
            "titulo":       doc.titulo,
            "aprovado_por": aprovado_por,
            "aprovado_em":  doc.aprovado_em.isoformat(),
            "chunks_total": len(chunks),
            "indexados":    indexados,
            "falhos":       falhos,
        }

    def rejeitar_documento(self, documento_id: int, aprovado_por: str, motivo: str) -> dict:
        doc = self.repo.rejeitar_documento(documento_id, aprovado_por, motivo)
        if not doc:
            return {"erro": "Documento não encontrado."}
        return {
            "documento_id":    doc.id,
            "status":          doc.status.value,
            "rejeitado_por":   aprovado_por,
            "motivo_rejeicao": motivo,
        }

    # ── Listagem ──────────────────────────────────────────────────────────────

    def listar_documentos(self, status: str = None) -> list[dict]:
        from app.database.models import DocumentoStatus
        filtro = DocumentoStatus(status) if status else None
        docs   = self.repo.listar_documentos(filtro)
        return [
            {
                "id":              d.id,
                "titulo":          d.titulo,
                "tipo":            d.tipo,
                "status":          d.status.value,
                "uploaded_by":     d.uploaded_by,
                "uploaded_at":     d.uploaded_at.isoformat(),
                "aprovado_por":    d.aprovado_por,
                "aprovado_em":     d.aprovado_em.isoformat() if d.aprovado_em else None,
                "motivo_rejeicao": d.motivo_rejeicao,
            }
            for d in docs
        ]

    def deletar_documento(self, documento_id: int) -> bool:
        return self.repo.deletar_documento(documento_id)

    # ── Busca RAG ─────────────────────────────────────────────────────────────

    def buscar_contexto(self, pergunta: str, limite: int = 5) -> list[dict]:
        fragmentos = self.repo.buscar_similares(pergunta, limite)
        return [
            {
                "fragmento_id": f.id,
                "documento_id": f.documento_id,
                "conteudo":     f.conteudo,
            }
            for f in fragmentos
        ]

    def salvar_fontes(self, resposta_id: int, fragmento_ids: list[int]) -> None:
        self.repo.salvar_fontes(resposta_id, fragmento_ids)