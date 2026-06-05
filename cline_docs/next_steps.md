# MusicBot — Status Completo do Projeto

## ✅ Já implementado

### Core
- [x] Flask API com blueprints (auth, chat, spotify, rag, dashboard)
- [x] PostgreSQL + pgvector
- [x] JWT com flask-jwt-extended (migrado de session)
- [x] Repository Pattern + Service Layer
- [x] Docker Compose (db, ollama, backend, frontend, tunnel)

### Autenticação
- [x] OAuth2 Spotify (PKCE) + login custom (email/senha)
- [x] Refresh automático do token Spotify
- [x] JWT no localStorage + authFetch

### Chat
- [x] Streaming SSE com histórico
- [x] Detecção de intenção Spotify → delega para Agent
- [x] Fallback RAG ou LLM puro
- [x] Export de conversas (txt, json, md, pdf)
- [x] Upload de arquivos (PDF, imagens, TXT)
- [x] RAG com síntese (create_stuff_documents_chain)
- [x] Memory do LangChain (DbChatMessageHistory)
- [x] Rota de feedback (POST /chat/feedback)

### LangChain Agents
- [x] 16 tools do Spotify (busca, playlists, playback, fila, dispositivo)
- [x] `return_direct=True` nas tools de execução
- [x] Streaming real via AgentExecutor.stream()
- [x] Resolução de dispositivo por nome

### Spotify API
- [x] Perfil, playlists, top tracks/artists, saved tracks
- [x] Busca de tracks e artistas
- [x] Playback (play, pause, next, previous, fila)
- [x] Dispositivos (listar, transferir, selecionar)
- [x] Criar playlist + criar playlist inteligente (com lista)
- [x] Adicionar na fila (individual e em lote)

### RAG
- [x] Embeddings com Sentence Transformers (google/embeddinggemma-300m)
- [x] Lazy loading thread-safe
- [x] Chunking com RecursiveCharacterTextSplitter
- [x] Busca vetorial com pgvector
- [x] Fluxo de aprovação/rejeição de documentos
- [x] Upload (texto, link, PDF)
- [x] Síntese com create_stuff_documents_chain

### Frontend
- [x] Chat com streaming, histórico, mini player
- [x] Profile com tracks recentes + tocar via API + seletor dispositivo
- [x] Base de conhecimento (conectada ao backend)
- [x] Dashboard com métricas
- [x] Auth (login, callback, registro)

### Extras
- [x] MCP Server (13 tools do Spotify)
- [x] Cloudflare Tunnel (container Docker com profile)
- [x] Scopes de playback adicionados

---

## ❌ Pendente

### 🔴 Prioridade Alta
1. **Conectar Chat.tsx com feedback backend**
   - Botão like/dislike → `POST /api/chat/feedback`
   - Modal report → `POST /api/chat/feedback` com comentário
   - Guardar `respostaId` nas mensagens

2. **Prune do Ollama / servidor IFES**
   - Modelo gemma4 pesado
   - Opção: trocar por modelo menor (gemma:2b, qwen:4b, llama3.2)
   - Ou conectar com servidor do IFES

### 🟡 Prioridade Média
3. **Sistema de recomendação**
   - Usar `/v1/recommendations` do Spotify
   - Integrar com ReccoBeats
   - Tool `recomendar_musicas(seed_tracks)`

4. **Wikipedia automático no RAG**
   - Quando RAG não achar info, baixar artigo da Wikipedia
   - Submeter como documento pendente
   - Tool `buscar_wikipedia(tema)`

### 🟢 Prioridade Baixa / Futuro
5. **Integração MusicBrainz/Last.fm/Genius**
   - Dados abertos sobre artistas
   - Letras de música
   - Tags e gêneros

6. **Melhorias no Profile.tsx**
   - Ver estado atual do playback
   - Mostrar o que está tocando agora
   - Controles (play/pause/next/prev) direto na página

---

## 💡 Sugestões de Melhoria no Código

### Backend

#### 1. `auth_guard.py` — _is_token_valid faz request externo a cada chamada
**Problema**: Toda requisição protegida faz `GET /v1/me` no Spotify pra ver se o token ainda é válido. Isso adiciona latência e consome rate limit.
**Sugestão**: Usar cache temporal (ex: 5 min) ou verificar apenas se o token não está nulo/vazio, e confiar no refresh se der 401.

#### 2. `chat/service.py` — Duplicação entre enviar_mensagem e stream_mensagem
**Problema**: Lógica de RAG + agent duplicada nos dois métodos (~80 linhas repetidas).
**Sugestão**: Extrair lógica comum (detectar_intenção, buscar RAG, etc.) para métodos privados compartilhados.

#### 3. `agents/tools.py` — Resolver dispositivo chama API a cada chamada
**Problema**: `_resolver_dispositivo()` chama `svc.get_devices()` (API Spotify) toda vez que toca uma música. Se o usuário falar "toca tal música" sem especificar dispositivo, faz request desnecessário.
**Sugestão**: Cachear lista de dispositivos com TTL (ex: 30s) ou só resolver dispositivo se o usuário mencionou explicitamente.

#### 4. `rag/sintese.py` — Chain não usa streaming
**Problema**: `create_stuff_documents_chain` usa `get_llm()` com `stream=False`, resposta vem completa. No `stream_mensagem()` do ChatService, o RAG com síntese não está sendo usado (só o modo antigo com chunks crus).
**Sugestão**: Integrar `RagSintese` no `stream_mensagem()` também, ou criar versão streaming.

#### 5. `chat/memory.py` — DbChatMessageHistory é read-only
**Problema**: O `DbChatMessageHistory` carrega do banco mas as mensagens adicionadas (add_message) ficam só em memória. Não persiste no banco.
**Sugestão**: Como as mensagens já são salvas pelo ChatRepository, o DbChatMessageHistory funciona bem como cache de leitura. Se for usar RunnableWithMessageHistory, pensar em como sincronizar.

#### 6. `chat/repository.py` — Sessões do banco abertas sequencialmente
**Problema**: Cada método abre e fecha sessão. Encadear get_historico + salvar_pergunta + salvar_resposta = 3 sessões.
**Sugestão**: Um método `salvar_pergunta_e_resposta()` que faz tudo em uma transação.

#### 7. `mcp_server.py` — Token fixo por env
**Problema**: `SPOTIFY_ACCESS_TOKEN` via env var. Token expira em 1h e o MCP server não faz refresh.
**Sugestão**: Implementar OAuth flow ou receber token via argumento.

### Frontend

#### 8. `Chat.tsx` — Muito grande (516 linhas)
**Problema**: Lógica de streaming, histórico, feedback, export, settings tudo no mesmo componente.
**Sugestão**: Extrair MiniPlayer, MessageList, FeedbackModal, DeviceSelector em componentes separados.

#### 9. `Profile.tsx` — Estilos inline
**Problema**: Objeto `styles` gigante com CSS inline. Difícil de manter.
**Sugestão**: Migrar para Tailwind classes ou CSS modules.

#### 10. `BaseConhecimento.tsx` — super_usuario_id hardcoded
**Problema**: `super_usuario_id: 1` fixo no submit. Se não existir SuperUsuario com ID 1 no banco, a requisição falha.
**Sugestão**: Criar SuperUsuario default no populate_mock_data.py ou permitir null e usar o moderador logado.