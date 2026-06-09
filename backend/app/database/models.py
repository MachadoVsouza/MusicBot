from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database.connection import Base
import enum

class ChatStatus(enum.Enum):
    ativo     = "ativo"
    arquivado = "arquivado"

class FeedbackTipo(enum.Enum):
    like    = "like"
    dislike = "dislike"
    report  = "report"

class ModeradorNivel(enum.Enum):
    editor        = "editor"
    administrador = "administrador"

class DocumentoStatus(enum.Enum):
    pendente  = "pendente"
    aprovado  = "aprovado"
    rejeitado = "rejeitado"

def now_utc():
    return datetime.now(timezone.utc)

class Usuario(Base):#USUARIO TEM EMAIL E SENHA OPCIONAIS MODIFICAR ISSO PROVAVLEMENTE PARA O LOGIN
    __tablename__ = "usuario"
    spotify_id            : Mapped[str]      = mapped_column(String, primary_key=True)
    email                 : Mapped[str|None] = mapped_column(String(255), nullable=True)
    password_hash         : Mapped[str|None] = mapped_column(Text, nullable=True)
    spotify_token         : Mapped[str|None] = mapped_column(Text)
    spotify_refresh_token : Mapped[str|None] = mapped_column(Text)
    llm_provider          : Mapped[str]      = mapped_column(String(10), default="local")  # "local" | "ifes"
    chats      : Mapped[list["Chat"]]      = relationship(back_populates="usuario")
    moderadores: Mapped[list["Moderador"]] = relationship(back_populates="usuario")

class SuperUsuario(Base):
    __tablename__ = "super_usuario"
    id   : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome : Mapped[str] = mapped_column(String(255))
    moderadores: Mapped[list["Moderador"]] = relationship(back_populates="super_usuario")
    documentos : Mapped[list["Documento"]] = relationship(back_populates="super_usuario")

class Moderador(Base):
    __tablename__ = "moderador"
    id               : Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id       : Mapped[str]            = mapped_column(ForeignKey("usuario.spotify_id"))
    super_usuario_id : Mapped[int]            = mapped_column(ForeignKey("super_usuario.id"))
    nivel            : Mapped[ModeradorNivel] = mapped_column(Enum(ModeradorNivel))
    usuario      : Mapped["Usuario"]      = relationship(back_populates="moderadores")
    super_usuario: Mapped["SuperUsuario"] = relationship(back_populates="moderadores")

class Chat(Base):
    __tablename__ = "chat"
    id         : Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id : Mapped[str]        = mapped_column(ForeignKey("usuario.spotify_id"))
    titulo     : Mapped[str]        = mapped_column(String(255), default="Nova conversa")
    created_at : Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at : Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    status     : Mapped[ChatStatus] = mapped_column(Enum(ChatStatus), default=ChatStatus.ativo)
    usuario  : Mapped["Usuario"]        = relationship(back_populates="chats")
    perguntas: Mapped[list["Pergunta"]] = relationship(back_populates="chat")

class Pergunta(Base):
    __tablename__ = "pergunta"
    id         : Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id    : Mapped[int]      = mapped_column(ForeignKey("chat.id"))
    conteudo   : Mapped[str]      = mapped_column(Text)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    chat    : Mapped["Chat"]            = relationship(back_populates="perguntas")
    resposta: Mapped["Resposta | None"] = relationship(back_populates="pergunta", uselist=False)

class Resposta(Base):
    __tablename__ = "resposta"
    id          : Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    pergunta_id : Mapped[int]      = mapped_column(ForeignKey("pergunta.id"))
    conteudo    : Mapped[str]      = mapped_column(Text)
    created_at  : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    usou_rag    : Mapped[bool]     = mapped_column(Boolean, default=False)
    pergunta : Mapped["Pergunta"]            = relationship(back_populates="resposta")
    feedbacks: Mapped[list["Feedback"]]      = relationship(back_populates="resposta")
    fontes   : Mapped[list["RespostaFonte"]] = relationship(back_populates="resposta")

class Feedback(Base):
    __tablename__ = "feedback"
    id          : Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    resposta_id : Mapped[int]          = mapped_column(ForeignKey("resposta.id"))
    usuario_id  : Mapped[str]          = mapped_column(ForeignKey("usuario.spotify_id"))
    tipo        : Mapped[FeedbackTipo] = mapped_column(Enum(FeedbackTipo))
    comentario  : Mapped[str|None]     = mapped_column(Text)
    created_at  : Mapped[datetime]     = mapped_column(DateTime(timezone=True), default=now_utc)
    resposta: Mapped["Resposta"] = relationship(back_populates="feedbacks")

class Documento(Base):
    __tablename__ = "documento"
    id               : Mapped[int]             = mapped_column(Integer, primary_key=True, autoincrement=True)
    super_usuario_id : Mapped[int]             = mapped_column(ForeignKey("super_usuario.id"))
    titulo           : Mapped[str]             = mapped_column(String(255))
    conteudo_original: Mapped[str]             = mapped_column(Text)
    tipo             : Mapped[str]             = mapped_column(String(50))
    status           : Mapped[DocumentoStatus] = mapped_column(Enum(DocumentoStatus), default=DocumentoStatus.pendente)
    ativo            : Mapped[bool]            = mapped_column(Boolean, default=True)
    # Tracking — envio
    uploaded_by : Mapped[str]      = mapped_column(ForeignKey("usuario.spotify_id"))
    uploaded_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    # Tracking — aprovação/rejeição
    aprovado_por    : Mapped[str|None]      = mapped_column(ForeignKey("usuario.spotify_id"), nullable=True)
    aprovado_em     : Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_rejeicao : Mapped[str|None]      = mapped_column(Text, nullable=True)
    super_usuario: Mapped["SuperUsuario"]    = relationship(back_populates="documentos")
    fragmentos   : Mapped[list["Fragmento"]] = relationship(back_populates="documento")

class Fragmento(Base):
    __tablename__ = "fragmento"
    id           : Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    documento_id : Mapped[int]  = mapped_column(ForeignKey("documento.id"))
    conteudo     : Mapped[str]  = mapped_column(Text)
    embedding    : Mapped[list] = mapped_column(Vector(768))
    documento: Mapped["Documento"]           = relationship(back_populates="fragmentos")
    fontes   : Mapped[list["RespostaFonte"]] = relationship(back_populates="fragmento")

class RespostaFonte(Base):
    __tablename__ = "resposta_fonte"
    id           : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resposta_id  : Mapped[int] = mapped_column(ForeignKey("resposta.id"))
    fragmento_id : Mapped[int] = mapped_column(ForeignKey("fragmento.id"))
    resposta : Mapped["Resposta"]  = relationship(back_populates="fontes")
    fragmento: Mapped["Fragmento"] = relationship(back_populates="fontes")


class AuditLog(Base):
    """Registro imutável de ações administrativas (aprovação, rejeição, criação de moderadores, etc.)."""
    __tablename__ = "audit_log"
    id          : Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id  : Mapped[str]      = mapped_column(ForeignKey("usuario.spotify_id"))
    acao        : Mapped[str]      = mapped_column(String(100))
    entidade    : Mapped[str]      = mapped_column(String(50))
    entidade_id : Mapped[int|None] = mapped_column(Integer, nullable=True)
    detalhes    : Mapped[str|None] = mapped_column(Text, nullable=True)
    ip          : Mapped[str|None] = mapped_column(String(45), nullable=True)
    created_at  : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
