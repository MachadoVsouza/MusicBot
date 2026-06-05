import json
from flask import Blueprint, request, Response, stream_with_context
from .service import ChatService
from app.core.auth_guard import require_auth
from app.core.http import success, error, not_found

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _svc() -> ChatService:
    return ChatService()


# ── Criar novo chat ───────────────────────────────────────────────────────────

@chat_bp.post("/")
@require_auth
def criar_chat(token: str, usuario_id: str):
    body   = request.get_json(silent=True) or {}
    titulo = body.get("titulo", "Nova conversa")
    return success(_svc().iniciar_chat(usuario_id, titulo), 201)


# ── Listar chats ──────────────────────────────────────────────────────────────

@chat_bp.get("/")
@require_auth
def listar_chats(token: str, usuario_id: str):
    return success({"chats": _svc().listar_chats(usuario_id)})


# ── Histórico de mensagens ────────────────────────────────────────────────────

@chat_bp.get("/<int:chat_id>/messages")
@require_auth
def get_mensagens(token: str, usuario_id: str, chat_id: int):
    resultado = _svc().get_mensagens(usuario_id, chat_id)
    if resultado is None:
        return not_found("Chat não encontrado")
    return success({"messages": resultado})


# ── Enviar mensagem (normal) ──────────────────────────────────────────────────

@chat_bp.post("/<int:chat_id>/message")
@require_auth
def enviar_mensagem(token: str, usuario_id: str, chat_id: int):
    body     = request.get_json(silent=True) or {}
    mensagem = body.get("mensagem", "").strip()

    if not mensagem:
        return error("Campo 'mensagem' obrigatório", 400, "missing_message")

    resultado = _svc().enviar_mensagem(usuario_id, chat_id, mensagem, token=token)
    if resultado is None:
        return not_found("Chat não encontrado")
    return success(resultado)


# ── Enviar mensagem com arquivo ───────────────────────────────────────────────

@chat_bp.post("/<int:chat_id>/message-with-file")
@require_auth
def enviar_mensagem_com_arquivo(token: str, usuario_id: str, chat_id: int):
    """
    Aceita mensagem + arquivo (PDF, imagem, TXT).
    Extrai o texto do arquivo e concatena com a mensagem.
    """
    mensagem = request.form.get("mensagem", "").strip()
    arquivo  = request.files.get("arquivo")

    if not mensagem and not arquivo:
        return error("Envie uma mensagem ou arquivo", 400)

    conteudo_extra = ""

    if arquivo:
        filename = arquivo.filename or ""
        ext      = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "pdf":
            conteudo_extra = _extrair_pdf(arquivo.read())
        elif ext in ("png", "jpg", "jpeg", "webp"):
            conteudo_extra = _extrair_imagem(arquivo.read(), ext)
        elif ext in ("txt", "md"):
            conteudo_extra = arquivo.read().decode("utf-8", errors="ignore")
        else:
            return error(f"Formato '{ext}' não suportado. Use PDF, imagem ou TXT.", 400)

    if conteudo_extra:
        mensagem = f"{mensagem}\n\n[Conteúdo do arquivo]:\n{conteudo_extra}" if mensagem else conteudo_extra

    resultado = _svc().enviar_mensagem(usuario_id, chat_id, mensagem, token=token)
    if resultado is None:
        return not_found("Chat não encontrado")
    return success(resultado)


# ── Streaming SSE ─────────────────────────────────────────────────────────────

@chat_bp.post("/<int:chat_id>/stream")
@require_auth
def stream_mensagem(token: str, usuario_id: str, chat_id: int):
    """
    Server-Sent Events — envia chunks de texto conforme o LLM gera.
    O frontend consome via EventSource ou fetch com ReadableStream.

    Formato de cada evento:
      data: {"chunk": "texto parcial"}
      data: {"done": true, "resposta_id": 123, "usou_rag": false}
    """
    body     = request.get_json(silent=True) or {}
    mensagem = body.get("mensagem", "").strip()

    if not mensagem:
        return error("Campo 'mensagem' obrigatório", 400)

    def generate():
        resultado = _svc().stream_mensagem(usuario_id, chat_id, mensagem, token=token)
        if resultado is None:
            yield f"data: {json.dumps({'erro': 'Chat não encontrado', 'done': True})}\n\n"
            return

        try:
            for chunk in resultado["stream"]:
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            import logging
            logging.error(f"Erro durante stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        resposta_id = resultado.get("resposta_id")
        midia       = resultado.get("midia")
        try:
            if "after_stream" in resultado:
                after_result = resultado["after_stream"]()
                # after_stream do agent retorna (resposta, midia)
                # after_stream do RAG retorna apenas resposta
                if isinstance(after_result, tuple):
                    resposta_obj, midia = after_result
                else:
                    resposta_obj = after_result
                resposta_id = resposta_obj.id if resposta_obj else resposta_id
        except Exception as e:
            import logging
            logging.error(f"Erro ao salvar resposta no after_stream: {e}")

        yield f"data: {json.dumps({'done': True, 'resposta_id': resposta_id, 'pergunta_id': resultado.get('pergunta_id'), 'usou_rag': resultado.get('usou_rag'), 'midia': midia})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":      "no-cache",
            "X-Accel-Buffering":  "no",
        },
    )


# ── Export do histórico ───────────────────────────────────────────────────────

@chat_bp.get("/<int:chat_id>/export")
@require_auth
def exportar_chat(token: str, usuario_id: str, chat_id: int):
    """
    Exporta o histórico do chat.
    ?format=txt | json | md | pdf (padrão: txt)
    """
    fmt       = request.args.get("format", "txt").lower()
    mensagens = _svc().get_mensagens(usuario_id, chat_id)

    if mensagens is None:
        return not_found("Chat não encontrado")

    if fmt == "json":
        content      = json.dumps({"chat_id": chat_id, "messages": mensagens}, ensure_ascii=False, indent=2)
        mimetype     = "application/json"
        filename     = f"chat_{chat_id}.json"
    elif fmt == "md":
        lines = [f"# Chat {chat_id}\n"]
        for m in mensagens:
            role  = "**Você**" if m["role"] == "user" else "**MusicBot**"
            lines.append(f"{role} ({m['timestamp']}):\n{m['content']}\n")
        content  = "\n---\n".join(lines)
        mimetype = "text/markdown"
        filename = f"chat_{chat_id}.md"
    elif fmt == "pdf":
        content  = _gerar_pdf(chat_id, mensagens)
        mimetype = "application/pdf"
        filename = f"chat_{chat_id}.pdf"
    else:  # txt
        lines = []
        for m in mensagens:
            role = "Você" if m["role"] == "user" else "MusicBot"
            lines.append(f"[{m['timestamp']}] {role}: {m['content']}")
        content  = "\n".join(lines)
        mimetype = "text/plain"
        filename = f"chat_{chat_id}.txt"

    return Response(
        content,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── Helpers de extração ───────────────────────────────────────────────────────

def _extrair_pdf(data: bytes) -> str:
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        return ""


def _extrair_imagem(data: bytes, ext: str) -> str:
    """
    Usa o Ollama vision (se o modelo suportar) para descrever a imagem.
    Se não suportar, retorna mensagem informativa.
    """
    try:
        import base64
        import requests
        from flask import current_app

        b64 = base64.b64encode(data).decode()
        resp = requests.post(
            f"{current_app.config['OLLAMA_BASE_URL']}/api/chat",
            json={
                "model":  current_app.config["OLLAMA_MODEL"],
                "stream": False,
                "messages": [{
                    "role":    "user",
                    "content": "Descreva o que você vê nesta imagem em português.",
                    "images":  [b64],
                }],
            },
            timeout=60,
        )
        if resp.ok:
            return resp.json()["message"]["content"]
    except Exception:
        pass
    return "[Imagem recebida — modelo atual não suporta visão]"


def _gerar_pdf(chat_id: int, mensagens: list[dict]) -> bytes:
    try:
        import io
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)

        styles = getSampleStyleSheet()
        user_style = ParagraphStyle(
            'UserMessage',
            parent=styles['Normal'],
            textColor='#0066cc',
            fontSize=11,
            spaceAfter=12,
            leftIndent=20,
        )
        bot_style = ParagraphStyle(
            'BotMessage',
            parent=styles['Normal'],
            textColor='#333333',
            fontSize=10,
            spaceAfter=12,
            leftIndent=20,
        )

        elements = []
        title = Paragraph(f"<b>Chat #{chat_id}</b>", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))

        for msg in mensagens:
            role = msg['role']
            timestamp = msg['timestamp']
            content = msg['content']

            label = "📌 Você" if role == "user" else "🤖 MusicBot"
            header = Paragraph(f"<b>{label}</b> <font size=8>({timestamp})</font>",
                             user_style if role == "user" else bot_style)
            elements.append(header)

            para = Paragraph(content, user_style if role == "user" else bot_style)
            elements.append(para)
            elements.append(Spacer(1, 0.2*inch))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}".encode()





# Nota: a rota /stream precisa ser atualizada para chamar after_stream
# após consumir o gerador. Substitui a função generate() na rota stream por:
#
# def generate():
#     resultado = _svc().stream_mensagem(...)
#     if resultado is None:
#         yield f"data: {json.dumps({'erro': 'Chat não encontrado'})}\n\n"
#         return
#
#     for chunk in resultado["stream"]:
#         yield f"data: {json.dumps({'chunk': chunk})}\n\n"
#
#     # Salva no banco após stream terminar
#     if "after_stream" in resultado:
#         resposta = resultado["after_stream"]()
#         resposta_id = resposta.id if resposta else None
#     else:
#         resposta_id = resultado.get("resposta_id")
#
#     yield f"data: {json.dumps({'done': True, 'resposta_id': resposta_id, ...})}\n\n"

