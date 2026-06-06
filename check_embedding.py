import sys, json
d = json.load(sys.stdin)
print('Embedding gerado!' if d.get('embedding') else 'ERRO: sem embedding')
if d.get('embedding'):
    print(f'Dimensoes: {len(d["embedding"])}')
