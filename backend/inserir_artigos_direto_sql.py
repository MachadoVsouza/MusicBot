#!/usr/bin/env python3
"""
inserir_artigos_final.py - Versão final corrigida
"""

import os
import sys
import random
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuração do banco
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://admin:admin@localhost:5432/MusicBot")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Caminho dos artigos
WIKIPEDIA_PATH = Path("/home/murilospalenza/MusicBot/wikipedia_files")

def gerar_embedding_falso(dimensoes=768):
    """Gera embedding falso para teste"""
    return [random.uniform(-1, 1) for _ in range(dimensoes)]

def dividir_em_fragmentos(conteudo, tamanho=1000, overlap=200):
    """Divide o texto em fragmentos"""
    fragmentos = []
    conteudo = conteudo.strip()
    
    if len(conteudo) <= tamanho:
        return [conteudo]
    
    paragrafos = conteudo.split('\n\n')
    atual = ""
    
    for paragrafo in paragrafos:
        if len(atual) + len(paragrafo) <= tamanho:
            if atual:
                atual += "\n\n" + paragrafo
            else:
                atual = paragrafo
        else:
            if atual:
                fragmentos.append(atual)
            palavras = atual.split()
            overlap_text = ' '.join(palavras[-overlap:]) if len(palavras) > overlap else atual
            atual = overlap_text + "\n\n" + paragrafo
    
    if atual:
        fragmentos.append(atual)
    
    return fragmentos if fragmentos else [conteudo[:tamanho]]

def inserir_documento(session, titulo, conteudo, super_usuario_id, usuario_uploader_id, usuario_aprovador_id):
    """Insere um documento e seus fragmentos no banco"""
    
    from app.database.models import Documento
    
    # Verifica se já existe
    existente = session.query(Documento).filter_by(titulo=titulo).first()
    if existente:
        print(f"  ⏭️  Documento já existe: {titulo}")
        return None
    
    # Cria o documento com todos os campos obrigatórios
    doc = Documento(
        super_usuario_id=super_usuario_id,
        titulo=titulo,
        conteudo_original=conteudo,
        tipo="wikipedia",
        status="aprovado",
        ativo=True,
        uploaded_by=usuario_uploader_id,  # spotify_id do usuário que enviou
        uploaded_at=datetime.now(),
        aprovado_por=usuario_aprovador_id,  # spotify_id do usuário que aprovou (tem que ser da tabela usuario)
        aprovado_em=datetime.now()
    )
    session.add(doc)
    session.flush()  # Gera o ID
    
    print(f"  📄 Documento criado: {titulo} (ID: {doc.id})")
    
    # Cria os fragmentos
    from app.database.models import Fragmento
    fragmentos_texto = dividir_em_fragmentos(conteudo)
    
    for i, frag_texto in enumerate(fragmentos_texto[:10]):  # Limita a 10 fragmentos
        frag = Fragmento(
            documento_id=doc.id,
            conteudo=frag_texto,
            embedding=gerar_embedding_falso()
        )
        session.add(frag)
    
    print(f"     ✂️  {len(fragmentos_texto[:10])} fragmentos criados")
    
    return doc.id

def main():
    print("=" * 60)
    print("🎵 MusicBot - Inserção Direta de Artigos da Wikipédia")
    print("=" * 60)
    
    # Verifica se a pasta existe
    if not WIKIPEDIA_PATH.exists():
        print(f"❌ Pasta não encontrada: {WIKIPEDIA_PATH}")
        return
    
    # Busca todos os arquivos .txt
    arquivos = list(WIKIPEDIA_PATH.rglob("*.txt"))
    
    if not arquivos:
        print(f"❌ Nenhum arquivo .txt encontrado em {WIKIPEDIA_PATH}")
        return
    
    print(f"\n📁 Encontrados {len(arquivos)} arquivos\n")
    
    # Conecta ao banco
    session = SessionLocal()
    
    try:
        from app.database.models import SuperUsuario, Usuario
        
        # 1. Verifica/existe super_usuario
        super_user = session.query(SuperUsuario).first()
        if not super_user:
            print("📝 Criando super usuário...")
            super_user = SuperUsuario(nome="Admin")
            session.add(super_user)
            session.commit()
            print(f"✅ Super usuário criado com ID: {super_user.id}")
        else:
            print(f"✅ Super usuário ID: {super_user.id}")
        
        # 2. Garantir que existe um usuário para ser o uploader
        usuario_uploader = session.query(Usuario).first()
        if not usuario_uploader:
            print("📝 Criando usuário para upload...")
            usuario_uploader = Usuario(
                spotify_id=f"uploader_{uuid.uuid4().hex[:8]}",
                spotify_token="fake_token",
                spotify_refresh_token="fake_refresh"
            )
            session.add(usuario_uploader)
            session.commit()
            print(f"✅ Usuário uploader criado: {usuario_uploader.spotify_id}")
        else:
            print(f"✅ Usuário uploader: {usuario_uploader.spotify_id}")
        
        # 3. Garantir que existe um usuário para ser o aprovador (pode ser o mesmo ou outro)
        usuario_aprovador = session.query(Usuario).offset(1).first()  # Tenta pegar outro
        if not usuario_aprovador:
            # Se não tem outro, cria um
            usuario_aprovador = Usuario(
                spotify_id=f"approver_{uuid.uuid4().hex[:8]}",
                spotify_token="fake_token",
                spotify_refresh_token="fake_refresh"
            )
            session.add(usuario_aprovador)
            session.commit()
            print(f"✅ Usuário aprovador criado: {usuario_aprovador.spotify_id}")
        else:
            print(f"✅ Usuário aprovador: {usuario_aprovador.spotify_id}")
        
        super_usuario_id = super_user.id
        usuario_uploader_id = usuario_uploader.spotify_id
        usuario_aprovador_id = usuario_aprovador.spotify_id
        
        # Insere cada artigo
        print("\n📚 Inserindo artigos...\n")
        
        inseridos = 0
        for arquivo in arquivos:
            # Lê o conteúdo
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Pega o título (nome do arquivo sem extensão)
            titulo = arquivo.stem
            
            # Insere
            doc_id = inserir_documento(session, titulo, conteudo, super_usuario_id, 
                                      usuario_uploader_id, usuario_aprovador_id)
            if doc_id:
                inseridos += 1
        
        # Commit final
        session.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ SUCESSO! {inseridos} documentos inseridos")
        print("=" * 60)
        
        # Resumo
        from app.database.models import Documento, Fragmento
        total_docs = session.query(Documento).count()
        total_frags = session.query(Fragmento).count()
        print(f"\n📊 Resumo no banco:")
        print(f"   - Documentos: {total_docs}")
        print(f"   - Fragmentos: {total_frags}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()
