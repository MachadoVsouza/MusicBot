# MusicBot — Status Completo do Projeto (atualizado 15/06/2026)

## ✅ Já implementado

### Infraestrutura
- [x] Flask API com blueprints (auth, chat, spotify, rag, dashboard, llm_provider)
- [x] PostgreSQL + pgvector
- [x] JWT com flask-jwt-extended
- [x] Repository Pattern + Service Layer
- [x] Docker Compose (db, ollama, backend, frontend, tunnel, pgadmin)

### Autenticação
- [x] OAuth2 Spotify (PKCE) + login custom (email/senha)
- [x] Refresh automático do token Spotify
- [x] JWT no localStorage + authFetch
- [x] Role-based access: user vs moderator
- [x] SuperUsuários fixos por ID (SUPER_USER_IDS)
- [x] **Recuperação de senha funcional** — JWT de 1h + envio email via SMTP (Gmail)

### Chat
- [x] Streaming SSE com histórico
- [x] Detecção de intenção Spotify → delega para Agent
- [x] Fallback RAG ou LLM puro
- [x] Export de conversas (txt, json, md, pdf)
- [x] Upload de arquivos (PDF, imagens, TXT)
- [x] RAG com síntese (create_stuff_documents_chain)
- [x] Memory do LangChain (DbChatMessageHistory)
- [x] Feedback (like/dislike/report)
- [x] **Markdown nas mensagens** (react-markdown + remark-gfm)
- [x] **Preferências persistentes** (localStorage)
- [x] **MiniPlayer** como componente independente

### LangChain Agents
- [x] 16 tools do Spotify (busca, playlists, playback, fila, dispositivo)
- [x] Streaming real via AgentExecutor.stream()

### Spotify API
- [x] Perfil, playlists, top tracks/artists, saved tracks
- [x] Playback (play, pause, next, previous, fila)
- [x] Dispositivos (listar, transferir, selecionar)

### RAG
- [x] Embeddings com Sentence Transformers
- [x] Chunking com RecursiveCharacterTextSplitter
- [x] Busca vetorial com pgvector
- [x] Fluxo de aprovação/rejeição de documentos
- [x] **Confirmação ao deletar documento**

### Frontend — Qualidade de Código
- [x] **TypeScript strict mode** (zero erros)
- [x] **Chat.tsx decomposto** em 7 componentes (MiniPlayer, MessageBubble, LLMProviderToggle, CommandsModal, PreferencesModal, ExportMenu, PlayOnSpotify)
- [x] **Centralização de tipos** em `src/types/index.ts`
- [x] **Padronização de imports** com `@/`
- [x] **Fonte unificada** (Figtree)
- [x] **ErrorBoundary global**
- [x] **memo()** em componentes puros (MusicbotLogo, AuthCard, MetricCard, EmptyTableRow)
- [x] **Toast unificado** (shadcn/ui, removido Sonner)
- [x] **App.css removido** (boilerplate Vite)
- [x] **Favicon corrigido** + lang="pt-BR"
- [x] PlayOnSpotify extraído para componente próprio
- [x] Keyframes movidos para `index.css`

### Extras
- [x] MCP Server (13 tools do Spotify)
- [x] Cloudflare Tunnel (container Docker com profile)
- [x] pgAdmin4 no docker-compose (porta 5050)
- [x] Toggle de provedor LLM (local/ifes)

---

## ❌ Pendente

### 🔴 Prioridade Alta — Backend
1. **Testar auto-detecção de artista Spotify**
2. **Prune do Ollama / servidor IFES** — modelo gemma4 pesado
3. **Refatorar agents/tools.py** — 19 tools aninhadas, zero testabilidade

### 🟡 Prioridade Média
4. **Sistema de recomendação** — `/v1/recommendations` do Spotify + ReccoBeats
5. **Wikipedia automático no RAG** — tool `buscar_wikipedia(tema)`
6. **Profile.tsx com Tailwind** — migrar CSS inline para classes utilitárias

### 🟢 Prioridade Baixa / Futuro
7. **Integração MusicBrainz/Last.fm/Genius**
8. **Lazy loading nas rotas** — `React.lazy()` para Chat, Dashboard, Profile
9. **Skeleton loading nas transições de rota**

---

## 💡 Sugestões de Melhoria no Código

### Backend (pendentes)

| # | Problema | Local | Sugestão |
|---|----------|-------|----------|
| 1 | Token validado a cada requisição | `auth_guard.py` | Cache TTL 5min |
| 2 | Lógica duplicada stream/não-stream | `chat/service.py` | Extrair método privado |
| 3 | 19 tools aninhadas | `agents/tools.py` | Separar em classes/arquivos |
| 4 | Sessões DB sequenciais | Repositories | Transação única |
| 5 | MCP server sem refresh token | `mcp_server.py` | OAuth flow |

### Frontend (pendentes)

| # | Problema | Local | Sugestão |
|---|----------|-------|----------|
| 6 | CSS inline (442 linhas) | `Profile.tsx` | Migrar para Tailwind |
| 7 | Sem code splitting | `App.tsx` | `React.lazy()` |
| 8 | Sem skeleton loading | Rotas | `Suspense` + fallback |