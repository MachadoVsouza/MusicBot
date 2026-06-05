#!/usr/bin/env python3
"""
Popula o banco de dados com dados fictícios para testes.
Agora utiliza os artigos da Wikipédia baixados pelo downloadWikipedia.py
Execute com: python3 -m app.database.populate_mock_data na pasta backend
"""

import os
import random
import sys
from datetime import timedelta
from pathlib import Path

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
NUM_FEEDBACKS_POR_RESPOSTA = 0.3
PROBABILIDADE_RESPOSTA_USOU_RAG = 0.6

# Configuração dos artigos da Wikipédia
WIKIPEDIA_BASE_PATH = Path("wikipedia_files")  # Pasta onde estão os artigos baixados
FRAGMENTOS_POR_DOCUMENTO = 5  # Número de fragmentos por documento
TAMANHO_FRAGMENTO = 1000  # Tamanho aproximado de cada fragmento em caracteres

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def gerar_token_spotify():
    """Gera um token falso."""
    return fake.pystr(min_chars=50, max_chars=120)

def gerar_embedding_falso(dimensoes=768):
    """Gera um vetor de embedding falso (lista de floats)."""
    return [random.uniform(-1, 1) for _ in range(dimensoes)]

def carregar_artigos_wikipedia():
    """
    Carrega todos os artigos da Wikipédia da pasta wikipedia_files/
    Retorna: lista de dicionários com {'titulo': ..., 'conteudo': ..., 'idioma': ..., 'caminho': ...}
    """
    artigos = []
    
    if not WIKIPEDIA_BASE_PATH.exists():
        print(f"⚠️ Pasta {WIKIPEDIA_BASE_PATH} não encontrada!")
        print("Execute primeiro o script downloadWikipedia.py para baixar os artigos.")
        return artigos
    
    # Percorre os diretórios de idioma (pt, en)
    for idioma_dir in WIKIPEDIA_BASE_PATH.iterdir():
        if not idioma_dir.is_dir():
            continue
        
        idioma = idioma_dir.name
        # Procura por arquivos .txt
        for arquivo in idioma_dir.glob("*.txt"):
            try:
                # Lê o conteúdo do artigo
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                
                # Extrai o título do nome do arquivo
                # Formato: Nome_do_Artigo_idioma.txt
                nome_arquivo = arquivo.stem
                titulo = nome_arquivo.replace(f'_{idioma}', '').replace('_', ' ')
                
                artigos.append({
                    'titulo': titulo,
                    'conteudo': conteudo,
                    'idioma': idioma,
                    'caminho': str(arquivo),
                    'tamanho': len(conteudo)
                })
                
                print(f"  📄 Carregado: {titulo} ({idioma}) - {len(conteudo)} caracteres")
                
            except Exception as e:
                print(f"  ❌ Erro ao ler {arquivo}: {e}")
    
    print(f"✅ Total de {len(artigos)} artigos carregados da Wikipédia")
    return artigos

def dividir_em_fragmentos(conteudo, tamanho_fragmento=TAMANHO_FRAGMENTO, overlap=100):
    """
    Divide o conteúdo em fragmentos menores com overlap.
    Tenta quebrar em parágrafos ou frases quando possível.
    """
    fragmentos = []
    
    # Primeiro tenta quebrar por parágrafos
    paragrafos = conteudo.split('\n\n')
    
    fragmento_atual = ""
    for paragrafo in paragrafos:
        paragrafo = paragrafo.strip()
        if not paragrafo:
            continue
            
        # Se adicionar este parágrafo ultrapassa o limite
        if len(fragmento_atual) + len(paragrafo) > tamanho_fragmento:
            if fragmento_atual:
                fragmentos.append(fragmento_atual.strip())
            
            # Inicia novo fragmento com overlap
            if overlap > 0 and len(fragmento_atual) > overlap:
                # Pega as últimas 'overlap' palavras do fragmento anterior
                palavras = fragmento_atual.split()
                overlap_text = ' '.join(palavras[-overlap:]) if len(palavras) > overlap else fragmento_atual
                fragmento_atual = overlap_text + "\n\n" + paragrafo
            else:
                fragmento_atual = paragrafo
        else:
            if fragmento_atual:
                fragmento_atual += "\n\n" + paragrafo
            else:
                fragmento_atual = paragrafo
    
    # Adiciona o último fragmento
    if fragmento_atual:
        fragmentos.append(fragmento_atual.strip())
    
    # Se nenhum fragmento foi criado (texto muito curto), cria um único fragmento
    if not fragmentos and conteudo:
        fragmentos = [conteudo[:tamanho_fragmento]]
    
    return fragmentos

# ============================================================
# FUNÇÕES DE CRIAÇÃO DOS MOCKS (mantidas originais)
# ============================================================
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

def criar_perguntas_e_respostas(session, chats, artigos_wikipedia=None):
    """
    Cria perguntas e suas respectivas respostas.
    Se artigos_wikipedia for fornecido, usa conteúdos reais para as respostas RAG.
    """
    perguntas = []
    respostas = []
    
    # Templates de perguntas baseadas nos artigos
    templates_perguntas = {
        'pt': [
            "Quem é o vocalista do {banda}?",
            "Quando o {banda} foi formado?",
            "Quais são os principais álbuns do {banda}?",
            "Qual é o estilo musical do {banda}?",
            "Quantos membros tem/tinha o {banda}?",
            "Qual foi o maior sucesso do {banda}?",
            "Onde o {banda} se originou?",
            "Por que o {banda} é famoso?",
            "Quem influenciou o {banda} musicalmente?",
            "Qual foi o último álbum do {banda}?"
        ],
        'en': [
            "Who is the lead singer of {banda}?",
            "When was {banda} formed?",
            "What are the main albums of {banda}?",
            "What is the musical style of {banda}?",
            "How many members does/did {banda} have?",
            "What was {banda}'s biggest hit?",
            "Where did {banda} originate?",
            "Why is {banda} famous?",
            "Who musically influenced {banda}?",
            "What was {banda}'s last album?"
        ]
    }
    
    # Mapeia títulos de artigos para conteúdo
    artigo_por_titulo = {}
    if artigos_wikipedia:
        for artigo in artigos_wikipedia:
            artigo_por_titulo[(artigo['titulo'].lower(), artigo['idioma'])] = artigo
    
    for chat in chats:
        for _ in range(NUM_PERGUNTAS_POR_CHAT):
            # Decidir se usa RAG ou não
            usou_rag = random.random() < PROBABILIDADE_RESPOSTA_USOU_RAG
            
            # Criar pergunta
            if usou_rag and artigos_wikipedia and random.random() > 0.3:
                # Usa um artigo real para gerar pergunta
                artigo = random.choice(artigos_wikipedia)
                idioma = artigo['idioma']
                templates = templates_perguntas.get(idioma, templates_perguntas['pt'])
                
                # Limpa o título (remove possíveis sufixos)
                titulo_banda = artigo['titulo'].split('(')[0].strip()
                
                # Escolhe um template e substitui {banda}
                template = random.choice(templates)
                pergunta_texto = template.format(banda=titulo_banda)
                
                # Gera resposta baseada no artigo
                resposta_conteudo = gerar_resposta_baseada_artigo(artigo, pergunta_texto)
                
                # Se não conseguiu gerar resposta específica, usa um trecho do artigo
                if not resposta_conteudo or len(resposta_conteudo) < 50:
                    resposta_conteudo = artigo['conteudo'][:1000]
                    
            else:
                # Pergunta fictícia
                pergunta_texto = fake.sentence(nb_words=10)
                resposta_conteudo = fake.paragraph(nb_sentences=5)
            
            pergunta = Pergunta(
                chat_id=chat.id,
                conteudo=pergunta_texto,
                created_at=fake.date_time_between(start_date=chat.created_at, end_date="now")
            )
            session.add(pergunta)
            session.flush()
            
            # Criar resposta vinculada à pergunta
            resposta = Resposta(
                pergunta_id=pergunta.id,
                conteudo=resposta_conteudo,
                usou_rag=usou_rag,
                created_at=pergunta.created_at + timedelta(seconds=random.randint(5, 120))
            )
            session.add(resposta)
            
            perguntas.append(pergunta)
            respostas.append(resposta)
    
    session.flush()
    print(f"Criados {len(perguntas)} Perguntas e {len(respostas)} Respostas")
    return perguntas, respostas

def gerar_resposta_baseada_artigo(artigo, pergunta):
    """Gera uma resposta simples baseada no artigo da Wikipédia."""
    # Implementação simples: extrai parágrafos relevantes
    conteudo = artigo['conteudo']
    
    # Palavras-chave comuns em perguntas
    palavras_chave = {
        'vocalista': ['vocal', 'singer', 'lead', 'frontman'],
        'formado': ['formed', 'formation', 'founded', 'origin'],
        'álbum': ['album', 'discography', 'record'],
        'estilo': ['style', 'genre', 'musical', 'influence'],
        'sucesso': ['hit', 'success', 'popular', 'famous']
    }
    
    # Tenta encontrar parágrafos relevantes
    paragrafos = conteudo.split('\n\n')
    melhor_paragrafo = None
    maior_score = 0
    
    for paragrafo in paragrafos[:10]:  # Limita aos primeiros parágrafos
        score = 0
        paragrafo_lower = paragrafo.lower()
        
        # Calcula score baseado nas palavras-chave da pergunta
        palavras_pergunta = pergunta.lower().split()
        for palavra in palavras_pergunta:
            if palavra in paragrafo_lower:
                score += 1
        
        if score > maior_score:
            maior_score = score
            melhor_paragrafo = paragrafo
    
    if melhor_paragrafo and maior_score > 0:
        return melhor_paragrafo[:1500]  # Limita o tamanho
    elif len(conteudo) > 500:
        return conteudo[:500] + "..."
    else:
        return conteudo

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

def criar_documentos_e_fragmentos(session, super_usuarios, usuarios, artigos_wikipedia):
    """
    Cria documentos e seus fragmentos usando os artigos da Wikipédia.
    """
    documentos = []
    fragmentos = []
    status_opts = [DocumentoStatus.aprovado]  # Todos aprovados por padrão
    
    # Se não há artigos, cria documentos fictícios
    if not artigos_wikipedia:
        print("⚠️ Nenhum artigo da Wikipédia encontrado. Criando documentos fictícios...")
        return criar_documentos_ficticios(session, super_usuarios, usuarios)
    
    for su in super_usuarios:
        for artigo in artigos_wikipedia:
            usuario_uploader = random.choice(usuarios)
            status = DocumentoStatus.aprovado  # Todos os artigos são automaticamente aprovados
            
            doc = Documento(
                super_usuario_id=su.id,
                titulo=f"{artigo['titulo']} ({artigo['idioma'].upper()})",
                conteudo_original=artigo['conteudo'],
                tipo="wikipedia_txt",
                status=status,
                ativo=True,
                uploaded_by=usuario_uploader.spotify_id,
                uploaded_at=fake.date_time_between(start_date="-30d", end_date="now"),
                aprovado_por=su.id,  # Super usuário aprova
                aprovado_em=fake.date_time_between(start_date="-20d", end_date="now")
            )
            
            session.add(doc)
            session.flush()  # Gera o ID do documento
            documentos.append(doc)
            
            # Divide o artigo em fragmentos
            fragmentos_conteudo = dividir_em_fragmentos(artigo['conteudo'], TAMANHO_FRAGMENTO)
            
            # Limita o número de fragmentos por documento
            for i, frag_conteudo in enumerate(fragmentos_conteudo[:FRAGMENTOS_POR_DOCUMENTO]):
                frag = Fragmento(
                    documento_id=doc.id,
                    conteudo=frag_conteudo,
                    embedding=gerar_embedding_falso(768),
                    metadata={
                        'idioma': artigo['idioma'],
                        'titulo': artigo['titulo'],
                        'posicao': i,
                        'total_fragmentos': len(fragmentos_conteudo[:FRAGMENTOS_POR_DOCUMENTO])
                    }
                )
                session.add(frag)
                fragmentos.append(frag)
    
    session.flush()
    print(f"Criados {len(documentos)} Documentos (da Wikipédia) e {len(fragmentos)} Fragmentos")
    return documentos, fragmentos

def criar_documentos_ficticios(session, super_usuarios, usuarios):
    """Fallback: cria documentos fictícios se não houver artigos da Wikipédia."""
    documentos = []
    fragmentos = []
    status_opts = list(DocumentoStatus)
    
    for su in super_usuarios:
        for i in range(5):  # 5 documentos fictícios
            usuario_uploader = random.choice(usuarios)
            status = random.choice(status_opts)
            conteudo = fake.paragraph(nb_sentences=20)
            
            doc = Documento(
                super_usuario_id=su.id,
                titulo=fake.sentence(nb_words=5)[:255],
                conteudo_original=conteudo,
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
        for _ in range(FRAGMENTOS_POR_DOCUMENTO):
            frag = Fragmento(
                documento_id=doc.id,
                conteudo=doc.conteudo_original[:500],
                embedding=gerar_embedding_falso(768)
            )
            session.add(frag)
            fragmentos.append(frag)
    
    session.flush()
    print(f"Criados {len(documentos)} Documentos fictícios e {len(fragmentos)} Fragmentos")
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
        
        # Carrega os artigos da Wikipédia
        print("\n📚 Carregando artigos da Wikipédia...")
        artigos_wikipedia = carregar_artigos_wikipedia()
        
        if artigos_wikipedia:
            print(f"\n✅ {len(artigos_wikipedia)} artigos carregados com sucesso!")
            print(f"📊 Total de caracteres: {sum(a['tamanho'] for a in artigos_wikipedia):,}")
        else:
            print("\n⚠️ Nenhum artigo encontrado. Continuando com dados fictícios...")
        
        print("\n--- Criando dados no banco ---\n")
        
        usuarios = criar_usuarios(session)
        super_usuarios = criar_super_usuarios(session)
        moderadores = criar_moderadores(session, usuarios, super_usuarios)
        chats = criar_chats(session, usuarios)
        perguntas, respostas = criar_perguntas_e_respostas(session, chats, artigos_wikipedia)
        feedbacks = criar_feedbacks(session, respostas, usuarios)
        documentos, fragmentos = criar_documentos_e_fragmentos(session, super_usuarios, usuarios, artigos_wikipedia)
        respostas_fontes = criar_respostas_fontes(session, respostas, fragmentos)

        session.commit()
        
        print("\n✅ POPULAÇÃO CONCLUÍDA COM SUCESSO!")
        print("\n📊 RESUMO FINAL:")
        print(f"   - Usuários: {len(usuarios)}")
        print(f"   - SuperUsuários: {len(super_usuarios)}")
        print(f"   - Moderadores: {len(moderadores)}")
        print(f"   - Chats: {len(chats)}")
        print(f"   - Perguntas: {len(perguntas)}")
        print(f"   - Respostas: {len(respostas)}")
        print(f"   - Feedbacks: {len(feedbacks)}")
        print(f"   - Documentos: {len(documentos)}")
        print(f"   - Fragmentos: {len(fragmentos)}")
        print(f"   - Relações Resposta-Fonte: {len(respostas_fontes)}")

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