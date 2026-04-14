from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, Integer, Boolean,
    ForeignKey, Enum, DateTime, Column, Table, UUID
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base
import uuid
import enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class ChatStatus(enum.Enum):
    ativo     = "ativo"
    arquivado = "arquivado"


class FeedbackTipo(enum.Enum):
    like    = "like"
    dislike = "dislike"
    report  = "report"


class UsuarioNivel(enum.Enum):
    usuario       = "usuario"
    editor        = "editor"
    administrador = "administrador"


# ── Helpers ───────────────────────────────────────────────────────────────────

def now_utc():
    return datetime.now(timezone.utc)


# ── Modelos ───────────────────────────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuario"

    id                    : Mapped[str]      = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email                 : Mapped[str]      = mapped_column(String(255), unique=True)
    password_hash         : Mapped[str|None] = mapped_column(Text, nullable=True)
    spotify_id            : Mapped[str|None] = mapped_column(String, unique=True, nullable=True)
    spotify_token         : Mapped[str|None] = mapped_column(Text, nullable=True)
    spotify_refresh_token : Mapped[str|None] = mapped_column(Text, nullable=True)
    created_at            : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    chats           : Mapped[list["Chat"]]      = relationship(back_populates="usuario")
    super_usuario   : Mapped["SuperUsuario|None"] = relationship(back_populates="usuario", uselist=False)
    feedback        : Mapped[list["Feedback"]]  = relationship(back_populates="usuario")
    documentos      : Mapped[list["Documento"]] = relationship(back_populates="uploaded_by_user")


class SuperUsuario(Base):
    __tablename__ = "super_usuario"

    id        : Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[str]      = mapped_column(UUID, ForeignKey("usuario.id"), unique=True)
    nivel     : Mapped[UsuarioNivel] = mapped_column(Enum(UsuarioNivel), default=UsuarioNivel.administrador)

    usuario    : Mapped["Usuario"] = relationship(back_populates="super_usuario")
    documentos : Mapped[list["Documento"]] = relationship(back_populates="super_usuario")


class Moderador(Base):
    __tablename__ = "moderador"

    id               : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id       : Mapped[str] = mapped_column(UUID, ForeignKey("usuario.id"))
    super_usuario_id : Mapped[int] = mapped_column(ForeignKey("super_usuario.id"))

    usuario      : Mapped["Usuario"]      = relationship()
    super_usuario: Mapped["SuperUsuario"] = relationship()


class Chat(Base):
    __tablename__ = "chat"

    id         : Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id : Mapped[str]        = mapped_column(UUID, ForeignKey("usuario.id"))
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

    chat    : Mapped["Chat"]           = relationship(back_populates="perguntas")
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
    usuario_id  : Mapped[str]          = mapped_column(UUID, ForeignKey("usuario.id"))
    tipo        : Mapped[FeedbackTipo] = mapped_column(Enum(FeedbackTipo))
    comentario  : Mapped[str|None]     = mapped_column(Text)
    created_at  : Mapped[datetime]     = mapped_column(DateTime(timezone=True), default=now_utc)

    resposta: Mapped["Resposta"] = relationship(back_populates="feedbacks")
    usuario : Mapped["Usuario"]  = relationship(back_populates="feedback")


class Documento(Base):
    __tablename__ = "documento"

    id                : Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    super_usuario_id  : Mapped[int]      = mapped_column(ForeignKey("super_usuario.id"))
    titulo            : Mapped[str]      = mapped_column(String(255))
    conteudo_original : Mapped[str]      = mapped_column(Text)
    tipo              : Mapped[str]      = mapped_column(String(50))
    uploaded_at       : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    uploaded_by       : Mapped[str]      = mapped_column(UUID, ForeignKey("usuario.id"))
    ativo             : Mapped[bool]     = mapped_column(Boolean, default=True)

    super_usuario: Mapped["SuperUsuario"]    = relationship(back_populates="documentos")
    uploaded_by_user: Mapped["Usuario"]      = relationship(back_populates="documentos")
    fragmentos   : Mapped[list["Fragmento"]] = relationship(back_populates="documento")


class Fragmento(Base):
    __tablename__ = "fragmento"

    id           : Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    documento_id : Mapped[int]      = mapped_column(ForeignKey("documento.id"))
    embedding    : Mapped[str|None] = mapped_column(Text)  # JSON por enquanto, pgvector no futuro

    documento: Mapped["Documento"]           = relationship(back_populates="fragmentos")
    fontes   : Mapped[list["RespostaFonte"]] = relationship(back_populates="fragmento")


class RespostaFonte(Base):
    __tablename__ = "resposta_fonte"

    id           : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resposta_id  : Mapped[int] = mapped_column(ForeignKey("resposta.id"))
    fragmento_id : Mapped[int] = mapped_column(ForeignKey("fragmento.id"))

    resposta : Mapped["Resposta"]  = relationship(back_populates="fontes")
    fragmento: Mapped["Fragmento"] = relationship(back_populates="fontes")