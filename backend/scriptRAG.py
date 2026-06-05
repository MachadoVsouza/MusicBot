#!/usr/bin/env python3
"""
upload_rag.py — Faz upload e aprovação de arquivos .txt para o RAG
Uso: 
    python3 scriptRAG.py /caminho/para/pasta
    python3 scriptRAG.py /caminho/para/pasta --jwt "seu_jwt_token"
    python3 scriptRAG.py /caminho/para/pasta --session "sua_session_cookie"
"""

import sys
import json
import requests
import argparse
from pathlib import Path
from typing import Optional

BASE_URL = "http://127.0.0.1:5000"
SUPER_USUARIO_ID = 1

# Tente importar o módulo de configuração para pegar o JWT da aplicação
try:
    # Tenta importar de diferentes lugares comuns
    sys.path.insert(0, str(Path(__file__).parent))
    from app.config import Config
    JWT_SECRET = Config.SECRET_KEY
    print("✅ Configuração carregada da aplicação")
except ImportError:
    try:
        from config import Config
        JWT_SECRET = Config.SECRET_KEY
        print("✅ Configuração carregada do config.py")
    except ImportError:
        JWT_SECRET = None
        print("⚠️ Não foi possível carregar configuração da aplicação")

def fazer_login_com_super_usuario() -> Optional[str]:
    """Tenta fazer login com super usuário para obter token/sessão"""
    print("🔐 Tentando login como super usuário...")
    
    # Tenta diferentes endpoints de login comuns
    endpoints = [
        f"{BASE_URL}/auth/login",
        f"{BASE_URL}/api/auth/login",
        f"{BASE_URL}/login",
        f"{BASE_URL}/superusuario/login"
    ]
    
    # Credenciais comuns de teste (ajuste conforme seu sistema)
    credenciais = [
        {"email": "admin@example.com", "senha": "admin123"},
        {"email": "super@example.com", "senha": "super123"},
        {"username": "admin", "password": "admin"},
        {"email": "teste@teste.com", "senha": "123456"}
    ]
    
    for endpoint in endpoints:
        for cred in credenciais:
            try:
                resp = requests.post(endpoint, json=cred, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # Tenta extrair token/sessão de diferentes formatos
                    token = data.get('token') or data.get('access_token') or data.get('jwt')
                    session_cookie = resp.cookies.get('session')
                    
                    if token:
                        print(f"✅ Token obtido via {endpoint}")
                        return token, 'token'
                    elif session_cookie:
                        print(f"✅ Sessão obtida via {endpoint}")
                        return session_cookie, 'session'
                    else:
                        print(f"⚠️ Login OK mas sem token/sessão: {data.keys()}")
                        
            except Exception as e:
                continue
    
    print("❌ Não foi possível fazer login automaticamente")
    return None, None

def upload_com_jwt(arquivo: Path, jwt_token: str) -> Optional[int]:
    """Upload usando JWT Bearer token"""
    print(f"📤 Enviando (JWT): {arquivo.stem}...")
    try:
        conteudo = arquivo.read_text(encoding="utf-8", errors="ignore")
        
        # Limita o tamanho se necessário
        if len(conteudo) > 10000:
            print(f"  ⚠️ Arquivo grande ({len(conteudo)} chars), truncando para 10000")
            conteudo = conteudo[:10000]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}"
        }
        
        resp = requests.post(
            f"{BASE_URL}/rag/documentos",
            json={
                "titulo": arquivo.stem,
                "tipo": "txt",
                "conteudo": conteudo,
                "super_usuario_id": SUPER_USUARIO_ID,
            },
            headers=headers,
            timeout=30,
        )
        
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            doc_id = data.get("documento_id")
            if doc_id:
                print(f"  ✅ Enviado! ID: {doc_id}")
                return doc_id
            else:
                print(f"  ⚠️ Resposta: {data}")
                return None
        else:
            print(f"  ❌ Erro: {resp.status_code} - {resp.text[:200]}")
            return None
            
    except Exception as e:
        print(f"  ❌ Falha: {e}")
        return None

def upload_com_session(arquivo: Path, session_cookie: str) -> Optional[int]:
    """Upload usando session cookie"""
    print(f"📤 Enviando (Session): {arquivo.stem}...")
    try:
        conteudo = arquivo.read_text(encoding="utf-8", errors="ignore")
        
        if len(conteudo) > 10000:
            print(f"  ⚠️ Arquivo grande ({len(conteudo)} chars), truncando para 10000")
            conteudo = conteudo[:10000]
        
        cookies = {"session": session_cookie}
        
        resp = requests.post(
            f"{BASE_URL}/rag/documentos",
            json={
                "titulo": arquivo.stem,
                "tipo": "txt",
                "conteudo": conteudo,
                "super_usuario_id": SUPER_USUARIO_ID,
            },
            cookies=cookies,
            timeout=30,
        )
        
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            doc_id = data.get("documento_id")
            if doc_id:
                print(f"  ✅ Enviado! ID: {doc_id}")
                return doc_id
            else:
                print(f"  ⚠️ Resposta: {data}")
                return None
        else:
            print(f"  ❌ Erro: {resp.status_code} - {resp.text[:200]}")
            return None
            
    except Exception as e:
        print(f"  ❌ Falha: {e}")
        return None

def upload_sem_auth(arquivo: Path) -> Optional[int]:
    """Upload sem autenticação (se a API permitir)"""
    print(f"📤 Enviando (Sem Auth): {arquivo.stem}...")
    try:
        conteudo = arquivo.read_text(encoding="utf-8", errors="ignore")
        
        if len(conteudo) > 10000:
            conteudo = conteudo[:10000]
        
        resp = requests.post(
            f"{BASE_URL}/rag/documentos",
            json={
                "titulo": arquivo.stem,
                "tipo": "txt",
                "conteudo": conteudo,
                "super_usuario_id": SUPER_USUARIO_ID,
            },
            timeout=30,
        )
        
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            doc_id = data.get("documento_id")
            if doc_id:
                print(f"  ✅ Enviado! ID: {doc_id}")
                return doc_id
            else:
                print(f"  ⚠️ Resposta: {data}")
                return None
        else:
            print(f"  ❌ Erro: {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"  ❌ Falha: {e}")
        return None

def aprovar(doc_id: int, auth_token: str = None, auth_type: str = 'token', session_cookie: str = None) -> None:
    """Aprova o documento usando o método de autenticação apropriado"""
    print(f"✅ Aprovando documento {doc_id}...")
    try:
        headers = {}
        cookies = {}
        
        if auth_type == 'token' and auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        elif auth_type == 'session' and session_cookie:
            cookies = {"session": session_cookie}
        
        resp = requests.post(
            f"{BASE_URL}/rag/documentos/{doc_id}/aprovar",
            headers=headers if headers else None,
            cookies=cookies if cookies else None,
            timeout=60,
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✅ Aprovado! Indexados: {data.get('indexados', 0)}")
        else:
            print(f"  ⚠️ Aprovação retornou {resp.status_code}: {resp.text[:100]}")
            
    except Exception as e:
        print(f"  ❌ Erro na aprovação: {e}")

def main():
    parser = argparse.ArgumentParser(description='Upload de arquivos TXT para o RAG')
    parser.add_argument('pasta', type=str, help='Caminho da pasta com arquivos .txt')
    parser.add_argument('--jwt', type=str, help='Token JWT para autenticação')
    parser.add_argument('--session', type=str, help='Session cookie para autenticação')
    parser.add_argument('--no-auth', action='store_true', help='Tentar sem autenticação')
    parser.add_argument('--auto-login', action='store_true', help='Tentar login automático')
    
    args = parser.parse_args()
    
    pasta = Path(args.pasta)
    if not pasta.exists():
        print(f"❌ Pasta não encontrada: {pasta}")
        sys.exit(1)
    
    arquivos = list(pasta.glob("*.txt"))
    if not arquivos:
        print(f"Nenhum arquivo .txt encontrado em {pasta}")
        return

    print(f"\n📁 {len(arquivos)} arquivo(s) encontrado(s) em {pasta}\n")
    
    # Determinar método de autenticação
    auth_token = None
    session_cookie = None
    auth_type = None
    
    if args.jwt:
        auth_token = args.jwt
        auth_type = 'token'
        print("🔑 Usando JWT fornecido via parâmetro")
    elif args.session:
        session_cookie = args.session
        auth_type = 'session'
        print("🍪 Usando session cookie fornecido via parâmetro")
    elif args.auto_login:
        print("🔄 Tentando login automático...")
        auth_token, auth_type = fazer_login_com_super_usuario()
        if auth_type == 'token':
            print("🔑 Token obtido via login automático")
        elif auth_type == 'session':
            session_cookie = auth_token
            auth_type = 'session'
            print("🍪 Session obtida via login automático")
        else:
            print("❌ Login automático falhou")
            args.no_auth = True
    elif args.no_auth:
        print("🌐 Tentando sem autenticação")
    else:
        # Tenta carregar do código automaticamente
        print("🔍 Tentando carregar autenticação do código...")
        
        # Tenta importar de diferentes lugares
        try:
            # Tenta importar do arquivo de configuração do Flask
            from flask import current_app
            if hasattr(current_app, 'config'):
                jwt_secret = current_app.config.get('SECRET_KEY')
                print("✅ Configuração carregada do Flask")
        except:
            pass
        
        # Se não conseguiu, pergunta ao usuário
        print("\n❌ Nenhum método de autenticação especificado!")
        print("\nOpções:")
        print("  1. Usar JWT: python3 scriptRAG.py /pasta --jwt 'seu_token'")
        print("  2. Usar Session: python3 scriptRAG.py /pasta --session 'cookie_valor'")
        print("  3. Login automático: python3 scriptRAG.py /pasta --auto-login")
        print("  4. Sem autenticação: python3 scriptRAG.py /pasta --no-auth")
        print("\nOu use o populate_mock_data.py diretamente (recomendado)")
        sys.exit(1)
    
    # Upload dos arquivos
    ids = []
    upload_func = None
    
    if auth_type == 'token':
        upload_func = lambda f: upload_com_jwt(f, auth_token)
    elif auth_type == 'session':
        upload_func = lambda f: upload_com_session(f, session_cookie)
    else:
        upload_func = upload_sem_auth
    
    for arquivo in arquivos:
        doc_id = upload_func(arquivo)
        if doc_id:
            ids.append(doc_id)
    
    if not ids:
        print("\n❌ Nenhum documento foi enviado.")
        print("\nSugestões:")
        print("  1. Verifique se o servidor está rodando")
        print("  2. Verifique se o super_usuario_id=1 existe no banco")
        print("  3. Tente com --no-auth se a API não requer autenticação")
        print("  4. Use o populate_mock_data.py diretamente")
        return
    
    print(f"\n📄 {len(ids)} documento(s) enviado(s). Aprovando...\n")
    
    for doc_id in ids:
        if auth_type == 'token':
            aprovar(doc_id, auth_token=auth_token, auth_type='token')
        elif auth_type == 'session':
            aprovar(doc_id, session_cookie=session_cookie, auth_type='session')
        else:
            aprovar(doc_id)
    
    print(f"\n✅ Concluído! {len(ids)} documento(s) processado(s).")

if __name__ == "__main__":
    main()