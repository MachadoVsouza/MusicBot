import re
import requests
from .repository import RagRepository

CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50


class RagService:
    def __init__(self):
        self.repo = RagRepository()

    # ── Extração de conteúdo ──────────────────────────────────────────────────

    def _extrair_de_url(self, url: str) -> str | None:
        """Baixa o conteúdo de uma URL e extrai o texto."""
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            # Remove tags HTML básicas
            texto = re.sub(r'<[^>]+>', ' ', resp.text)
            texto = re.sub(r'\s+', ' ', texto).strip()
            return texto[:50000]  # limita para não explodir o banco
        except Exception:
            return None

    def _extrair_de_pdf(self, conteudo_bytes: bytes) -> str | None:
        """Extrai texto de um PDF em bytes usando pypdf."""
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(conteudo_bytes))
            texto  = "\n".join(page.extract_text() or "" for page in reader.pages)
            return texto.strip()
        except Exception:
            return None

    # ── Chunking ──────────────────────────────────────────────────────────────

    def _chunk_text(self, texto: str) -> list[str]:
        texto      = re.sub(r'\n{3,}', '\n\n', texto.strip())
        paragrafos = texto.split('\n\n')
        chunks     = []
        atual      = ""

        for paragrafo in paragrafos:
            if len(atual) + len(paragrafo) <= CHUNK_SIZE:
                atual += paragrafo + "\n\n"
            else:
                if atual:
                    chunks.append(atual.strip())
                    atual = atual[-CHUNK_OVERLAP:] + paragrafo + "\n\n"
                else:
                    for i in range(0, len(paragrafo), CHUNK_SIZE - CHUNK_OVERLAP):
                        chunks.append(paragrafo[i:i + CHUNK_SIZE].strip())
                    atual = ""

        if atual.strip():
            chunks.append(atual.strip())

        return [c for c in chunks if len(c) > 20]

    # ── Upload — salva como pendente ──────────────────────────────────────────

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
        """
        Recebe o documento do usuário e salva como PENDENTE.
        Verifica duplicata antes de salvar.
        Extrai conteúdo de URL ou PDF se fornecido.
        """
        # Extrai conteúdo conforme o tipo
        if tipo == "link" and url:
            conteudo = self._extrair_de_url(url)
            if not conteudo:
                return {"erro": "Não foi possível extrair conteúdo da URL."}

        elif tipo == "pdf" and pdf_bytes:
            conteudo = self._extrair_de_pdf(pdf_bytes)
            if not conteudo:
                return {"erro": "Não foi possível extrair texto do PDF."}

        # Verifica duplicata usando o primeiro chunk como amostra
        amostra = conteudo[:500]
        if self.repo.verificar_duplicata(amostra):
            return {
                "duplicata": True,
                "mensagem":  "Já existe conteúdo similar na base de conhecimento.",
            }

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

    # ── Aprovação — indexa os chunks ──────────────────────────────────────────

    def aprovar_e_indexar(self, documento_id: int, aprovado_por: str) -> dict:
        """
        Moderador aprova o documento.
        Marca como aprovado e indexa os chunks no banco.
        """
        doc = self.repo.aprovar_documento(documento_id, aprovado_por)
        if not doc:
            return {"erro": "Documento não encontrado."}

        chunks    = self._chunk_text(doc.conteudo_original)
        indexados = 0
        falhos    = 0

        for chunk in chunks:
            resultado = self.repo.salvar_fragmento(doc.id, chunk)
            if resultado:
                indexados += 1
            else:
                falhos += 1

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
            "documento_id":   doc.id,
            "status":         doc.status.value,
            "rejeitado_por":  aprovado_por,
            "motivo_rejeicao": motivo,
        }

    # ── Listagem ──────────────────────────────────────────────────────────────

    def listar_documentos(self, status: str = None) -> list[dict]:
        from app.database.models import DocumentoStatus
        filtro = DocumentoStatus(status) if status else None
        docs   = self.repo.listar_documentos(filtro)
        return [
            {
                "id":             d.id,
                "titulo":         d.titulo,
                "tipo":           d.tipo,
                "status":         d.status.value,
                "uploaded_by":    d.uploaded_by,
                "uploaded_at":    d.uploaded_at.isoformat(),
                "aprovado_por":   d.aprovado_por,
                "aprovado_em":    d.aprovado_em.isoformat() if d.aprovado_em else None,
                "motivo_rejeicao": d.motivo_rejeicao,
            }
            for d in docs
        ]

    def deletar_documento(self, documento_id: int) -> bool:
        return self.repo.deletar_documento(documento_id)

    # ── Busca RAG ─────────────────────────────────────────────────────────────

    def buscar_contexto(self, pergunta: str, limite: int = 3) -> list[dict]:
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
