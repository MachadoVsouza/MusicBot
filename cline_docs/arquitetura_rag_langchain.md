# Arquitetura RAG + LangChain — MusicBot

## 1. O que é RAG (Retrieval-Augmented Generation)

RAG é uma técnica que combina **busca vetorial** com **LLM**. Em vez do modelo responder apenas com o que "sabe" de treinamento, ele primeiro busca documentos relevantes numa base de conhecimento e usa esse conteúdo como contexto para gerar a resposta.

**Fluxo no MusicBot:**
```
Mensagem do usuário
  → detecta se é pergunta normal (não Spotify)
  → busca fragmentos similares no PostgreSQL (pgvector) por similaridade de cosine
  → monta prompt com contexto + pergunta
  → envia para o Ollama (gemma4:e4b)
  → LLM responde baseado no contexto
```

---

## 2. LangChain — o que é

LangChain é um framework para construir aplicações com LLMs. Fornece:
- **Model I/O**: interface padronizada para LLMs (Ollama, OpenAI, etc.)
- **Retrieval**: splitters, embeddings, vector stores
- **Agents**: ferramentas que o LLM pode chamar (tool calling)
- **Chains**: pipelines de processamento

## 3. LangChain 1.x — Mudanças Drásticas

Entre 2024 e 2025, o LangChain passou por uma reestruturação completa:

| Versão | Mudança |
|---|---|
| 0.2.x → 0.3.x | `langchain.text_splitter` extraído para `langchain-text-splitters` |
| 0.3.x → 1.0 | `langchain.chains` removido para `langchain-community` |
| 1.0 | `langchain.memory` removido para `langchain_community.chat_message_histories` |
| 1.0 | `langchain.agents` parcialmente quebrado (alguns imports mudaram) |

**Status no MusicBot (após correções):**
- ✅ `rag/service.py` → usa `langchain_text_splitters`
- ✅ `rag/sintese.py` → **não usa mais LangChain chains**. Chama o LLM direto via `llm.invoke()`
- ✅ `agents/service.py` → **não usa mais AgentExecutor**. Usa `llm.bind_tools()` + chain simples
- ✅ `chat/memory.py` → usa `langchain_community.chat_message_histories`
- ✅ `requirements.txt` → dependências completas: `langchain`, `langchain-core`, `langchain-ollama`, `langchain-community`, `langchain-text-splitters`

---

## 4. Estrutura do RAG no MusicBot

```
frontend/BaseConhecimento.tsx (upload de docs + aprovação)
  ↕ HTTP (JWT)
backend/rag/blueprint.py (rotas: POST /rag/documentos, GET /rag/documentos, POST /rag/documentos/<id>/aprovar)
  ↕
backend/rag/service.py (lógica: submeter, chunking, aprovar, indexar, buscar)
  ↕
backend/rag/repository.py (SQL: salvar docs, fragmentos, busca vetorial)
  ↕
PostgreSQL + pgvector (tabelas: documento, fragmento, resposta_fonte)
```

### Fluxo de upload:
1. Moderador envia documento (txt, link, PDF)
2. `RagService.submeter_documento()` extrai texto, verifica duplicata, salva como `pendente`
3. Moderador aprova → `RagService.aprovar_e_indexar()` faz chunking e gera embeddings
4. Fragmentos + embeddings salvos no banco com índice vetorial

### Fluxo de busca no Chat:
1. Mensagem do usuário (sem intenção Spotify) → `RagSintese.consultar()`
2. Busca top-5 fragmentos similares via `embedding <=> :emb` (distância cosseno)
3. Monta prompt com `<contexto>...</contexto>` + pergunta
4. Chama `llm.invoke()` do Ollama
5. Retorna resposta sintetizada + fontes

---

## 5. Embeddings

**Atual:** via Ollama (`/api/embeddings`) usando o modelo `gemma4:e4b`.
- Prós: sem dependência extra, roda na mesma GPU do LLM
- Contras: qualidade inferior ao `google/embeddinggemma-300m`

**Futuro:** reimplementar `google/embeddinggemma-300m` com SentenceTransformers na GPU.
- Commit de referência: código original em `backend/app/rag/client.py` antes de 05/06/2026
- Dockerfile: `pip install git+https://github.com/huggingface/transformers@v4.56.0-Embedding-Gemma-preview`
- Desafio: container precisa de GPU e ~1.5GB de RAM extra
- A qualidade dos embeddings é superior, especialmente para domínio musical

---

## 6. Performance

- **Índice vetorial:** `ivfflat` com `lists=100` na coluna `embedding` da tabela `fragmento` (criado em 05/06/2026)
- **Batch de embeddings:** chamadas individuais ao Ollama (otimização pendente: paralelizar ou usar batch)
- **Chunking:** `RecursiveCharacterTextSplitter` (chunk=600, overlap=100)
- **Busca:** distância cosseno com pgvector, limitada a 5 resultados

---

## 7. Problemas Conhecidos

1. **BaseConhecimento** — `super_usuario_id` fixo como `1`, precisa existir no banco
2. **Aprovar documento** — `gemma4:e4b` não suporta `/api/embeddings`, precisa trocar para `nomic-embed-text`
3. **PDF no chat** — modelo atual não tem suporte a vision, imagens viram placeholder
4. **Queries lentas** — resolvido com índice IVFFlat (só funciona se houver dados na tabela)

---

## 8. Comandos Úteis

```bash
# Puxar modelo de embeddings compatível com Ollama
docker exec MusicBot_Ollama ollama pull nomic-embed-text

# Criar índice vetorial manualmente
docker compose exec db psql -U admin -d MusicBot \
  -c "CREATE INDEX IF NOT EXISTS idx_fragmento_embedding ON fragmento USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"

# Verificar tamanho das tabelas
docker compose exec db psql -U admin -d MusicBot \
  -c "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"