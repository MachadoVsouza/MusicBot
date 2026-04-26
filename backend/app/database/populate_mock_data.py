#!/usr/bin/env python3
"""
Popula o banco de dados com dados fictícios para testes.
Execute com: python3 -m app.database.populate_mock_data na pasta backend
"""

import os
import random
import sys
from datetime import timedelta

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database.models import (
    Usuario, SuperUsuario, Moderador, Chat, Pergunta, Resposta,
    Feedback, Documento, Fragmento, RespostaFonte,
    ChatStatus, FeedbackTipo, ModeradorNivel, DocumentoStatus
)

# ============================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://admin:admin@localhost:5432/MusicBot")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# ============================================================
# CONFIGURAÇÃO DOS MOCKS
# ============================================================
fake = Faker("pt_BR")
Faker.seed(42)
random.seed(42)

# Quantidades
NUM_SUPER_USUARIOS = 2
NUM_USUARIOS = 20
NUM_MODERADORES_POR_SUPER = 2
NUM_CHATS_POR_USUARIO = 3
NUM_PERGUNTAS_POR_CHAT = 4
NUM_DOCUMENTOS_POR_SUPER = 5
NUM_FRAGMENTOS_POR_DOC = 3
NUM_FEEDBACKS_POR_RESPOSTA = 0.3
PROBABILIDADE_RESPOSTA_USOU_RAG = 0.6

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def gerar_token_spotify():
    """Gera um token falso."""
    return fake.pystr(min_chars=50, max_chars=120)


def gerar_embedding_falso(dimensoes=768):
    """Gera um vetor de embedding falso (lista de floats)."""
    return [random.uniform(-1, 1) for _ in range(dimensoes)]


def criar_usuarios(session):
    """Cria usuários com spotify_id como primary key."""
    usuarios = []
    for _ in range(NUM_USUARIOS):
        us = Usuario(
            spotify_id=f"spotify_{fake.uuid4()}",
            spotify_token=gerar_token_spotify(),
            spotify_refresh_token=gerar_token_spotify()
        )
        session.add(us)
        usuarios.append(us)
    session.flush()
    print(f"Criados {len(usuarios)} Usuários")
    return usuarios


def criar_super_usuarios(session):
    """Cria SuperUsuários."""
    super_usuarios = []
    for _ in range(NUM_SUPER_USUARIOS):
        su = SuperUsuario(
            nome=fake.name()
        )
        session.add(su)
        super_usuarios.append(su)
    session.flush()
    print(f"Criados {len(super_usuarios)} SuperUsuários")
    return super_usuarios


def criar_moderadores(session, usuarios, super_usuarios):
    """Cria moderadores vinculados a usuarios e super_usuarios."""
    moderadores = []
    niveis = list(ModeradorNivel)
    
    for su in super_usuarios:
        for i in range(NUM_MODERADORES_POR_SUPER):
            if i < len(usuarios):
                usuario = usuarios[i]
                mod = Moderador(
                    usuario_id=usuario.spotify_id,
                    super_usuario_id=su.id,
                    nivel=random.choice(niveis)
                )
                session.add(mod)
                moderadores.append(mod)
    
    session.flush()
    print(f"Criados {len(moderadores)} Moderadores")
    return moderadores


def criar_chats(session, usuarios):
    """Cria chats vinculados aos usuários."""
    chats = []
    status_opts = list(ChatStatus)
    
    for usuario in usuarios:
        for _ in range(NUM_CHATS_POR_USUARIO):
            chat = Chat(
                usuario_id=usuario.spotify_id,
                titulo=fake.sentence(nb_words=4)[:255],
                status=random.choice(status_opts),
                created_at=fake.date_time_between(start_date="-30d", end_date="now")
            )
            session.add(chat)
            chats.append(chat)
    session.flush()
    print(f"Criados {len(chats)} Chats")
    return chats


def criar_perguntas_e_respostas(session, chats):
    """Cria perguntas e suas respectivas respostas."""
    perguntas = []
    respostas = []
    
    for chat in chats:
        for _ in range(NUM_PERGUNTAS_POR_CHAT):
            # Criar pergunta
            pergunta = Pergunta(
                chat_id=chat.id,
                conteudo=fake.sentence(nb_words=10),
                created_at=fake.date_time_between(start_date=chat.created_at, end_date="now")
            )
            session.add(pergunta)
            session.flush()  # Gera o ID da pergunta
            
            # Criar resposta vinculada à pergunta
            resposta = Resposta(
                pergunta_id=pergunta.id,  # Usa o ID gerado
                conteudo=fake.paragraph(nb_sentences=5),
                usou_rag=random.random() < PROBABILIDADE_RESPOSTA_USOU_RAG,
                created_at=pergunta.created_at + timedelta(seconds=random.randint(5, 120))
            )
            session.add(resposta)
            
            perguntas.append(pergunta)
            respostas.append(resposta)
    
    session.flush()
    print(f"Criados {len(perguntas)} Perguntas e {len(respostas)} Respostas")
    return perguntas, respostas


def criar_feedbacks(session, respostas, usuarios):
    """Cria feedbacks para as respostas."""
    feedbacks = []
    tipos = list(FeedbackTipo)
    
    for resposta in respostas:
        if random.random() < NUM_FEEDBACKS_POR_RESPOSTA:
            usuario = random.choice(usuarios)
            fb = Feedback(
                resposta_id=resposta.id,
                usuario_id=usuario.spotify_id,
                tipo=random.choice(tipos),
                comentario=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
                created_at=resposta.created_at + timedelta(hours=random.randint(1, 72))
            )
            session.add(fb)
            feedbacks.append(fb)
    
    session.flush()
    print(f"Criados {len(feedbacks)} Feedbacks")
    return feedbacks


def criar_documentos_e_fragmentos(session, super_usuarios, usuarios):
    """Cria documentos e seus fragmentos com embeddings."""
    documentos = []
    fragmentos = []
    status_opts = list(DocumentoStatus)
    
    for su in super_usuarios:
        for _ in range(NUM_DOCUMENTOS_POR_SUPER):
            usuario_uploader = random.choice(usuarios)
            status = random.choice(status_opts)
            
            doc = Documento(
                super_usuario_id=su.id,
                titulo=fake.sentence(nb_words=5)[:255],
                conteudo_original=fake.paragraph(nb_sentences=20),
                tipo=random.choice(["pdf", "txt", "md", "docx"]),
                status=status,
                ativo=random.choice([True, True, True, False]),
                uploaded_by=usuario_uploader.spotify_id,
                uploaded_at=fake.date_time_between(start_date="-30d", end_date="now")
            )
            
            if status == DocumentoStatus.aprovado:
                doc.aprovado_por = random.choice(usuarios).spotify_id
                doc.aprovado_em = doc.uploaded_at + timedelta(days=random.randint(1, 5))
            elif status == DocumentoStatus.rejeitado:
                doc.motivo_rejeicao = fake.sentence(nb_words=10)
            
            session.add(doc)
            documentos.append(doc)
    
    session.flush()
    
    for doc in documentos:
        for _ in range(NUM_FRAGMENTOS_POR_DOC):
            frag = Fragmento(
                documento_id=doc.id,
                conteudo=doc.conteudo_original[:500],
                embedding=gerar_embedding_falso(768)
            )
            session.add(frag)
            fragmentos.append(frag)
    
    session.flush()
    print(f"Criados {len(documentos)} Documentos e {len(fragmentos)} Fragmentos")
    return documentos, fragmentos


def criar_respostas_fontes(session, respostas, fragmentos):
    """Relaciona respostas a fragmentos (para RAG)."""
    respostas_fontes = []
    
    for resposta in respostas:
        if resposta.usou_rag and fragmentos:
            num_fontes = random.randint(1, min(3, len(fragmentos)))
            fragmentos_escolhidos = random.sample(fragmentos, min(num_fontes, len(fragmentos)))
            
            for frag in fragmentos_escolhidos:
                rf = RespostaFonte(
                    resposta_id=resposta.id,
                    fragmento_id=frag.id
                )
                session.add(rf)
                respostas_fontes.append(rf)
    
    session.flush()
    print(f"Criados {len(respostas_fontes)} RespostaFonte")
    return respostas_fontes


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================
def main():
    print("Conectando ao banco...")
    session = SessionLocal()

    try:
        resposta = input("Deseja apagar todas as tabelas e recriar? (s/N): ").strip().lower()
        if resposta == "s":
            print("Recriando tabelas...")
            from app.database.connection import Base
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            print("Tabelas recriadas com sucesso!")

        print("\n--- Iniciando população com dados mock ---\n")

        usuarios = criar_usuarios(session)
        super_usuarios = criar_super_usuarios(session)
        moderadores = criar_moderadores(session, usuarios, super_usuarios)
        chats = criar_chats(session, usuarios)
        perguntas, respostas = criar_perguntas_e_respostas(session, chats)
        feedbacks = criar_feedbacks(session, respostas, usuarios)
        documentos, fragmentos = criar_documentos_e_fragmentos(session, super_usuarios, usuarios)
        respostas_fontes = criar_respostas_fontes(session, respostas, fragmentos)

        session.commit()
        
        print("\n✅ POPULAÇÃO CONCLUÍDA COM SUCESSO!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERRO durante a população: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()