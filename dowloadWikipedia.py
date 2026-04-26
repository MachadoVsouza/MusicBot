from os import mkdir
import wikipedia
import os

# ============================================
# CONFIGURAÇÕES
# ============================================

# Lista das bandas (artigos) a serem baixados
bandas = [
    "The Beatles", "Queen", "Pink Floyd", "The Rolling Stones",
    "Led Zeppelin", "Nirvana", "Metallica", "Radiohead",
    "The Doors", "Geese", "Black Country, New Road", "Calcinha Preta", "Legião Urbana", "Racionais MC's"
]

# Idiomas desejados: (código, nome_da_pasta)
idiomas = [
    ("en", "en"),   # (código da Wikipédia, nome da subpasta)
    ("pt", "pt")
]

# ============================================
# FUNÇÃO PRINCIPAL
# ============================================

def baixar_artigos(artigos, idiomas):
    """
    Baixa artigos da Wikipédia em múltiplos idiomas.
    
    Args:
        artigos (list): Lista de títulos dos artigos.
        idiomas (list): Lista de tuplas (codigo_idioma, nome_pasta).
    """

    # Pasta principal
    pasta_principal = "wikipedia_files"
    os.makedirs(pasta_principal, exist_ok=True)

    # Criar pastas para cada idioma (se não existirem)
    for _, pasta in idiomas:
        os.makedirs(os.path.join(pasta_principal, pasta), exist_ok=True)

    for artigo in artigos:
        print(f"\n--- Processando: {artigo} ---")
        nome_base = artigo.replace(' ', '_')

        for codigo, pasta in idiomas:
            nome_arquivo = f"{nome_base}_{codigo}.txt"
            caminho = os.path.join(pasta_principal, pasta, nome_arquivo)  # CORRIGIDO: inclui pasta_principal

            # Verificar se já existe
            if os.path.exists(caminho):
                print(f"  ⏭ {caminho} já existe. Pulando.")
                continue

            # Tentar baixar
            try:
                wikipedia.set_lang(codigo)
                pagina = wikipedia.page(artigo)
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(pagina.content)
                print(f"  ✔ Salvo: {caminho}")
            except wikipedia.exceptions.DisambiguationError as e:
                print(f"  ✘ [{codigo.upper()}] Página ambígua: {e.options[:3]}...")
            except wikipedia.exceptions.PageError:
                print(f"  ✘ [{codigo.upper()}] Página não encontrada.")
            except Exception as e:
                print(f"  ✘ [{codigo.upper()}] Erro inesperado: {e}")

    print("\n✅ Processamento concluído!")

# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    baixar_artigos(bandas, idiomas)