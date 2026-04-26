"""
upload_rag.py — Faz upload e aprovação de arquivos .txt para o RAG
Uso: python3 upload_rag.py /caminho/para/pasta
"""

import sys
import json
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000"
SESSION  = "8J_J75y6mm_Bf3qucDPR_6kG0X44E_7bW5zS-WwW77U.6s8UIRjBhr9o5CsAtwPRacEMZZQ"
SUPER_USUARIO_ID = 1

cookies = {"session": SESSION}


def upload(arquivo: Path) -> int | None:
    print(f"📤 Enviando: {arquivo.stem}...")
    try:
        conteudo = arquivo.read_text(encoding="utf-8", errors="ignore")
        resp = requests.post(
            f"{BASE_URL}/rag/documentos",
            json={
                "titulo":           arquivo.stem,
                "tipo":             "txt",
                "conteudo":         conteudo,
                "super_usuario_id": SUPER_USUARIO_ID,
            },
            cookies=cookies,
            timeout=30,
        )
        data = resp.json()

        if data.get("duplicata"):
            print(f"  ⚠️  Duplicata ignorada: {arquivo.stem}")
            return None

        if "erro" in data:
            print(f"  ❌ Erro: {data['erro']}")
            return None

        doc_id = data.get("documento_id")
        print(f"  ✅ Enviado! ID: {doc_id} | Status: {data.get('status')}")
        return doc_id

    except Exception as e:
        print(f"  ❌ Falha: {e}")
        return None


def aprovar(doc_id: int) -> None:
    print(f"🔍 Aprovando documento {doc_id}...")
    try:
        resp = requests.post(
            f"{BASE_URL}/rag/documentos/{doc_id}/aprovar",
            cookies=cookies,
            timeout=60,
        )
        data = resp.json()
        print(f"  ✅ Aprovado! Chunks: {data.get('indexados')} indexados, {data.get('falhos')} falhos")
    except Exception as e:
        print(f"  ❌ Falha ao aprovar: {e}")


def main():
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    arquivos = list(pasta.glob("*.txt"))

    if not arquivos:
        print(f"Nenhum arquivo .txt encontrado em {pasta}")
        return

    print(f"\n📁 {len(arquivos)} arquivo(s) encontrado(s) em {pasta}\n")

    ids = []
    for arquivo in arquivos:
        doc_id = upload(arquivo)
        if doc_id:
            ids.append(doc_id)

    if not ids:
        print("\nNenhum documento novo para aprovar.")
        return

    print(f"\n⏳ Aprovando {len(ids)} documento(s)...\n")
    for doc_id in ids:
        aprovar(doc_id)

    print(f"\n🎉 Concluído! {len(ids)} documento(s) indexado(s).")


if __name__ == "__main__":
    main()
EOF
