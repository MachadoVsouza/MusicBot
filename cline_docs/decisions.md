# Decisões Técnicas

## Estrutura
- Separação clara em módulos (auth, chat, spotify, rag, dashboard, reccobeats)
- Repository Pattern para abstrair banco de dados
- Blueprint Pattern do Flask para organização de rotas

## Autenticação
- JWT com flask-jwt-extended (migrado de Flask-Session)
- `auth_guard.py` usa `verify_jwt_in_request()` + busca spotify_token do banco
- Refresh automático do token Spotify via `_try_refresh()` no auth_guard
- `repository.py` session só guarda PKCE temporário (state)
- Callback Spotify redireciona para `/auth/callback?token=<jwt>`
- Frontend salva JWT no `localStorage`, `authFetch` injeta `Authorization: Bearer`
- OAuth2 Spotify para integração musical
- Guards de autenticação via decorator (`@require_auth`)

## Frontend
- React + TypeScript com Vite
- Tailwind CSS + shadcn/ui para componentes
- Context API para estado global (AuthContext)
- Streaming SSE para respostas do chat
- authFetch como helper global de requisições autenticadas

## Dados
- PostgreSQL (pgvector) como banco principal
- SQLAlchemy como ORM
- Docker para ambiente padronizado

## LLM / LangChain
- Ollama como provedor local (gemma4:e4b)
- `num_predict=2048`, `temperature=0.7`, `keep_alive="30m"`
- Prompts reescritos para respostas detalhadas e sem corte
- LangChain Agents (tool calling) para integração Spotify via `create_tool_calling_agent`
- `max_iterations=5`, `handle_parsing_errors=True`

## RAG (Retrieval-Augmented Generation)
- Embeddings: Sentence Transformers (google/embeddinggemma-300m)
- Lazy loading do modelo com Lock (thread-safe)
- Batch de embeddings com `normalize_embeddings=True`
- Chunking via `RecursiveCharacterTextSplitter` do LangChain
- Busca ordenada por ranking vetorial (distância cosseno via pgvector)
- Suporte a documentos: texto, PDF, URLs
- Fluxo de aprovação: pendente → aprovado/rejeitado com indexação sob demanda
- Verificação de duplicata via similaridade vetorial (threshold 0.15)

## Playback / Preview de Áudio
- Spotify **não retorna mais `preview_url` para a maioria das tracks** (deprecated desde 2024)
- Para fazer playback real é necessário **Spotify Web Playback SDK** (Premium) no frontend
- A SDK requer scopes extras: `user-modify-playback-state`, `user-read-playback-state`
- Alternativa futura: criar um **Agente de Playback** que usa o SDK no frontend para controlar dispositivos Spotify do usuário