# Decisões Técnicas

## Estrutura
- Separação clara em módulos (auth, chat, spotify, rag, dashboard, reccobeats)
- Repository Pattern para abstrair banco de dados
- Blueprint Pattern do Flask para organização de rotas

## Embeddings (RAG)
- **Atualmente**: embeddings via Ollama (`/api/embeddings` com o modelo gemma4:e4b) — mais leve, sem dependência extra
- **Futuro**: reimplementar `google/embeddinggemma-300m` com **SentenceTransformers rodando na GPU** para melhor qualidade
  - Commit de referência: antes de 05/06/2026 (quando `rag/client.py` usava SentenceTransformers)
  - Dockerfile tinha `pip install git+https://github.com/huggingface/transformers@v4.56.0-Embedding-Gemma-preview`
  - Desafio: container precisa de acesso à GPU (nvidia-docker) e ~1.5GB extras de RAM

## Autenticação
- JWT com flask-jwt-extended (migrado de Flask-Session)
- `auth_guard.py` usa `verify_jwt_in_request()` + busca spotify_token do banco
- Refresh automático do token Spotify via `_try_refresh()` no auth_guard
- `repository.py` session só guarda PKCE temporário (state)
- Callback Spotify redireciona para `/auth/callback?token=<jwt>`
- Frontend salva JWT no `localStorage`, `authFetch` injeta `Authorization: Bearer`
- OAuth2 Spotify para integração musical
- Guards de autenticação via decorator (`@require_auth`)
- Sessão Flask com `SameSite=Lax` + nginx `proxy_pass_header Set-Cookie` para resolver `state_invalido`
- **Role-based access**: `/api/auth/me` retorna `role` e `super_usuario_id`; detecção automática de artista Spotify (`type: "artist"`) → cria SuperUsuario
- **SuperUsuários fixos**: `SUPER_USER_IDS` no config com IDs de desenvolvedor (`818da73b30404df29b817237bd1a936c`, `b5727e21ded847928278e6fe1782060f`); fallback no `/me` com `garantir_super_usuario_para_id_fixo()` para criar registro no banco sob demanda
- **Problema conhecido**: `_is_token_valid()` faz GET /v1/me a cada requisição, consumindo rate limit

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
- `return_direct=True` nas tools de execução (tocar, pausar, fila, etc.) — resposta direta sem LLM gerar texto extra

## RAG (Retrieval-Augmented Generation)
- Embeddings: Sentence Transformers (google/embeddinggemma-300m) com lazy loading thread-safe
- Batch de embeddings com `normalize_embeddings=True`
- Chunking via `RecursiveCharacterTextSplitter` do LangChain
- Busca ordenada por ranking vetorial (distância cosseno via pgvector)
- Suporte a documentos: texto, PDF, URLs
- Fluxo de aprovação: pendente → aprovado/rejeitado com indexação sob demanda
- Verificação de duplicata via similaridade vetorial (threshold 0.15)
- **Síntese**: `create_stuff_documents_chain` do LangChain em vez de chunks crus no prompt

## Memory do LangChain
- `DbChatMessageHistory` implementa `BaseChatMessageHistory` do LangChain
- Carrega do banco PostgreSQL (tabelas Pergunta/Resposta)
- Cache em memória (`_history_cache`) para evitar recarregar do DB a cada chamada
- **Nota**: DbChatMessageHistory é read-only (add_message só vai pra memória). Persistência real é feita pelo ChatRepository

## Playback / Preview de Áudio
- Spotify **não retorna mais `preview_url` para a maioria das tracks** (deprecated desde 2024)
- Para fazer playback real é necessário usar a **API REST player** (`/v1/me/player/play`) no backend
- A API de player requer scopes extras: `user-modify-playback-state`, `user-read-playback-state`
- Implementado: devices (listar/transferir), play (track/context), pause, next, previous, queue
- Resolução de dispositivo por nome via `_resolver_dispositivo()` no tools.py

## MCP Server
- Servidor MCP standalone (não roda dentro do Flask)
- 13 tools do Spotify expostas: buscar/tocar música, pausar, próximo/anterior, dispositivos, playlists, artista, recentes, top músicas
- Token via env var `SPOTIFY_ACCESS_TOKEN` (problema: token expira em 1h, não tem refresh)

## Cloudflare Tunnel
- Container Docker separado com `--profile tunnel`
- Usa cloudflared para criar túnel trycloudflare.com gratuito
- **Limitação**: A cada novo link, precisa adicionar redirect URI no Dashboard do Spotify Developer
- Nginx configurado com `proxy_buffering off` e `chunked_transfer_encoding on` para SSE

## Importante: Spotify Web API — Consultas Futuras

### OpenAPI Spec Oficial
**URL**: `https://developer.spotify.com/reference/web-api/open-api-schema.yaml`
- Spec OpenAPI 3.0 completa com todos endpoints, schemas, auth e parâmetros
- Pode ser usada diretamente com AI tools (Claude, ChatGPT, Cursor) ou geradores de código

### Guia "Building with AI"
**URL**: `https://developer.spotify.com/documentation/web-api/tutorials/building-with-ai`
Guia oficial do Spotify com recomendações para integrar a API com LLMs

### Endpoints Deprecated — NÃO USAR
Ao mexer na API do Spotify, evitar estes endpoints:
- ❌ `GET /playlists/{id}/tracks` → ✅ usar `GET /playlists/{id}/items`
- ❌ `POST /playlists/{id}/tracks` → ✅ usar `POST /playlists/{id}/items`
- ❌ `PUT /playlists/{id}/tracks` → ✅ usar `PUT /playlists/{id}/items`
- ❌ `DELETE /playlists/{id}/tracks` → ✅ usar `DELETE /playlists/{id}/items`
- ❌ Endpoints específicos de library por tipo → ✅ usar `/me/library`
- ❌ Implicit Grant flow → ✅ usar Authorization Code with PKCE

### Regras Gerais
1. **OAuth Flow**: PKCE para dados de usuário. Client Credentials apenas para dados públicos. Nunca Implicit Grant
2. **Redirect URIs**: Sempre HTTPS (exceto `http://127.0.0.1` para dev local). Nunca `http://localhost` ou wildcards
3. **Scopes**: Mínimos necessários. Scopes amplos = violação de menor privilégio
4. **Token management**: Client Secret nunca em client-side. Implementar refresh sempre
5. **Rate limits**: Exponential backoff + respeitar `Retry-After` header em HTTP 429
6. **Error handling**: Tratar todos os códigos HTTP do OpenAPI spec
7. **Termos**: Não cachear conteúdo além do necessário. Sempre atribuir ao Spotify. Não usar API para treinar ML

### Checklist ao revisar código Spotify
- [ ] OAuth flow correto? (PKCE para user data, Client Credentials para público)
- [ ] Redirect URIs com HTTPS?
- [ ] Scopes mínimos necessários?
- [ ] Tokens armazenados com segurança? Client Secret fora do client-side?
- [ ] Rate limits com exponential backoff?
- [ ] Tratamento de todos os HTTP errors?
- [ ] Endpoints atuais (não deprecated)?
- [ ] Sem cache excessivo, atribuição correta?