#!/usr/bin/env python3
"""
Popula o banco de dados com dados fictícios para testes.
Execute com: python3 -m app.database.populate_mock_data na pasta backend
#necessita de ser um modulo porem nao e entao o -m resolve

"""

import os
import random
import sys
from datetime import timedelta

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajuste o caminho do import conforme sua estrutura
# Exemplo: se o script está na raiz do projeto, use:
from app.database.models import (
    Usuario, SuperUsuario, Moderador, UsuarioNivel,
    Chat, ChatStatus, Pergunta, Resposta, Feedback, FeedbackTipo,
    Documento, Fragmento, RespostaFonte, now_utc
)

# ============================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================
# Altere para a URL do seu banco real ou deixe SQLite para testes locais
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://admin:admin@localhost:5432/MusicBot")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# ============================================================
# CONFIGURAÇÃO DOS MOCKS
# ============================================================
fake = Faker("pt_BR")          # Para dados em português (nomes, textos)
Faker.seed(42)                 # Para reproducibilidade
random.seed(42)

# Quantidades (ajuste conforme necessidade)
NUM_SUPER_USUARIOS = 2
NUM_USUARIOS = 20
NUM_MODERADORES_POR_SUPER = 2   # total = super * este valor
NUM_CHATS_POR_USUARIO = 3
NUM_PERGUNTAS_POR_CHAT = 4      # cada pergunta terá 1 resposta
NUM_DOCUMENTOS_POR_SUPER = 5
NUM_FRAGMENTOS_POR_DOC = 3
NUM_FEEDBACKS_POR_RESPOSTA = 0.3  # probabilidade (30% das respostas)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def gerar_token_spotify():
    """Gera um token falso parecido com o real."""
    return fake.pystr(min_chars=50, max_chars=120)


def gerar_embedding_falso():
    """Retorna uma string JSON representando um vetor de 1536 dimensões (mock)."""
    import json
    vetor = [random.uniform(-1, 1) for _ in range(128)]  # 128 dimensões para não pesar
    return json.dumps(vetor)


def criar_super_usuarios(session, usuarios):
    """Cria SuperUsuarios vinculados a usuarios existentes."""
    super_usuarios = []
    niveis = list(UsuarioNivel)
    for i in range(min(NUM_SUPER_USUARIOS, len(usuarios))):
        usuario = usuarios[i]
        su = SuperUsuario(
            usuario_id=usuario.id,
            nivel=UsuarioNivel.administrador
        )
        session.add(su)
        super_usuarios.append(su)
    session.flush()  # para obter os ids
    print(f"Criados {len(super_usuarios)} SuperUsuarios")
    return super_usuarios


def criar_usuarios(session):
    """Cria usuarios com a nova estrutura (UUID id, email, senha hash nullable)."""
    usuarios = []
    for _ in range(NUM_USUARIOS):
        us = Usuario(
            email=fake.email(),
            password_hash=None,  # Usuários via Spotify não têm senha
            spotify_id=f"spotify_{fake.uuid4()}",
            spotify_token=gerar_token_spotify(),
            spotify_refresh_token=gerar_token_spotify()
        )
        session.add(us)
        usuarios.append(us)
    session.flush()
    print(f"Criados {len(usuarios)} Usuarios")
    return usuarios


def criar_moderadores(session, usuarios, super_usuarios):
    """Cria moderadores vinculados a usuarios e super_usuarios."""
    moderadores = []
    for su in super_usuarios:
        for _ in range(NUM_MODERADORES_POR_SUPER):
            usuario = random.choice(usuarios)
            # Evitar duplicidade de (usuario_id, super_usuario_id) se quiser, mas não é obrigatório
            mod = Moderador(
                usuario_id=usuario.id,
                super_usuario_id=su.id,
            )
            session.add(mod)
            moderadores.append(mod)
    session.flush()
    print(f"Criados {len(moderadores)} Moderadores")
    return moderadores


def criar_chats(session, usuarios):
    """Cria chats vinculados aos usuarios pelo novo usuario_id (UUID)."""
    chats = []
    status_opts = list(ChatStatus)
    for usuario in usuarios:
        for _ in range(NUM_CHATS_POR_USUARIO):
            chat = Chat(
                usuario_id=usuario.id,
                titulo=fake.sentence(nb_words=4)[:255],
                status=random.choice(status_opts),
                created_at=fake.date_time_between(start_date="-30d", end_date="now"),
                updated_at=fake.date_time_between(start_date="-30d", end_date="now")
            )
            session.add(chat)
            chats.append(chat)
    session.flush()
    print(f"Criados {len(chats)} Chats")
    return chats


def criar_perguntas_e_respostas(session, chats):
    perguntas = []
    respostas = []
    for chat in chats:
        for _ in range(NUM_PERGUNTAS_POR_CHAT):
            pergunta = Pergunta(
                chat_id=chat.id,
                conteudo=fake.sentence(nb_words=10),
                created_at=fake.date_time_between(start_date=chat.created_at, end_date="now")
            )
            session.add(pergunta)
            perguntas.append(pergunta)
            # Cria a resposta associada via relacionamento (não via ID)
            resposta = Resposta(
                pergunta=pergunta,  # ← MUDANÇA IMPORTANTE: use o objeto, não o ID
                conteudo=fake.paragraph(nb_sentences=5),
                usou_rag=random.choice([True, False]),
                created_at=pergunta.created_at + timedelta(seconds=random.randint(5, 120))
            )
            session.add(resposta)
            respostas.append(resposta)
    # Agora o flush vai inserir perguntas primeiro, pegar os IDs, depois inserir respostas
    session.flush()
    return perguntas, respostas


def criar_feedbacks(session, respostas, usuarios):
    """Cria feedbacks vinculados a respostas e usuarios pelo novo usuario_id (UUID)."""
    feedbacks = []
    tipos = list(FeedbackTipo)
    for resposta in respostas:
        if random.random() < NUM_FEEDBACKS_POR_RESPOSTA:
            usuario = random.choice(usuarios)
            fb = Feedback(
                resposta_id=resposta.id,
                usuario_id=usuario.id,
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
    """Cria documentos vinculados a super_usuarios e usuarios pelo novo uploaded_by (UUID)."""
    documentos = []
    fragmentos = []
    for su in super_usuarios:
        for _ in range(NUM_DOCUMENTOS_POR_SUPER):
            doc = Documento(
                super_usuario_id=su.id,
                titulo=fake.sentence(nb_words=5)[:255],
                conteudo_original=fake.paragraph(nb_sentences=20),
                tipo=random.choice(["pdf", "txt", "md", "docx"]),
                uploaded_by=random.choice(usuarios).id,
                ativo=random.choice([True, True, True, False])  # 75% ativo
            )
            session.add(doc)
            documentos.append(doc)
    session.flush()
    # Fragmentos
    for doc in documentos:
        for _ in range(NUM_FRAGMENTOS_POR_DOC):
            frag = Fragmento(
                documento_id=doc.id,
                embedding=gerar_embedding_falso()
            )
            session.add(frag)
            fragmentos.append(frag)
    session.flush()
    print(f"Criados {len(documentos)} Documentos e {len(fragmentos)} Fragmentos")
    return documentos, fragmentos


def criar_respostas_fontes(session, respostas, fragmentos):
    """Relaciona respostas a fragmentos (mock de RAG)."""
    respostas_fontes = []
    for resposta in respostas:
        # Só cria se a resposta usou RAG e se existem fragmentos
        if resposta.usou_rag and fragmentos:
            # Cada resposta pode referenciar 1-3 fragmentos aleatórios
            num_fontes = random.randint(1, min(3, len(fragmentos)))
            for _ in range(num_fontes):
                frag = random.choice(fragmentos)
                rf = RespostaFonte(
                    resposta_id=resposta.id,
                    fragmento_id=frag.id
                )
                session.add(rf)
                respostas_fontes.append(rf)
    session.flush()
    print(f"Criados {len(respostas_fontes)} RespostaFonte (relações resposta↔fragmento)")
    return respostas_fontes


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================
def main():
    print("Conectando ao banco...")
    session = SessionLocal()

    try:
        # Limpeza opcional (cuidado! comente se não quiser apagar dados)
        resposta = input("Deseja apagar todas as tabelas e recriar? (s/N): ").strip().lower()
        if resposta == "s":
            print("Recriando tabelas...")
            from app.database.connection import Base
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)

        print("\n--- Iniciando população com dados mock ---\n")

        # 1. Usuarios (nenhuma dependência)
        usuarios = criar_usuarios(session)
        # 2. SuperUsuarios (depende de usuarios)
        super_usuarios = criar_super_usuarios(session, usuarios)
        # 3. Moderadores (depende de usuarios e super_usuarios)
        moderadores = criar_moderadores(session, usuarios, super_usuarios)
        # 4. Chats (depende de usuarios)
        chats = criar_chats(session, usuarios)
        # 5. Perguntas e Respostas (depende de chats)
        perguntas, respostas = criar_perguntas_e_respostas(session, chats)
        # 6. Feedbacks (depende de respostas e usuarios)
        feedbacks = criar_feedbacks(session, respostas, usuarios)
        # 7. Documentos e Fragmentos (depende de super_usuarios e usuarios)
        documentos, fragmentos = criar_documentos_e_fragmentos(session, super_usuarios, usuarios)
        # 8. RespostaFonte (depende de respostas e fragmentos)
        respostas_fontes = criar_respostas_fontes(session, respostas, fragmentos)

        session.commit()
        print("\n✅ População concluída com sucesso!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERRO durante a população: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()