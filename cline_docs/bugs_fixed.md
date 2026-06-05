# Bugs Corrigidos

## [05/06/2026] - Sessão 2: Playback, Streaming e JWT

### 1. Spotify blueprint sem url_prefix (CAUSA RAIZ de Profile quebrado)
- **Arquivo**: `backend/app/spotify/blueprint.py`
- **Problema**: `Blueprint("spotify", __name__)` → rotas em `/profile`, não em `/spotify/profile`
- **Solução**: Adicionado `url_prefix="/spotify"`
- **Impacto**: Frontend chamava `/api/spotify/profile` → Vite transformava em `/spotify/profile` → Flask devolvia 404 porque a rota era `/profile`

### 2. Refresh token sem client_secret
- **Arquivo**: `backend/app/core/auth_guard.py`
- **Problema**: `_try_refresh()` enviava só `client_id`, sem `client_secret`
- **Solução**: Adicionado `"client_secret": cfg["SPOTIFY_CLIENT_SECRET"]`
- **Impacto**: Token Spotify expirava, refresh falhava, require_auth retornava 401

### 3. fetchMe no AuthContext sem prefixo /api
- **Arquivo**: `frontend/src/contexts/AuthContext.tsx`
- **Problema**: `fetch('/auth/me')` nunca chegava no backend (nginx/Vite só roteiam `/api/*`)
- **Solução**: `fetch('/api/auth/me')`

### 4. loginWithToken não carregava perfil do usuário
- **Arquivo**: `frontend/src/contexts/AuthContext.tsx`
- **Problema**: Só validava token, nunca buscava dados do Spotify para popular user
- **Solução**: Após validar JWT, faz fetch de `/api/spotify/profile` e popula setUser

### 5. Inconsistência de chaves usuario_id vs spotify_id
- **Arquivo**: `backend/app/auth/service.py` + `auth/blueprint.py`
- **Problema**: `register_user()` e `login_with_password()` retornavam `{"usuario_id": ...}` mas valor era spotify_id
- **Solução**: Renomeado para `{"spotify_id": ...}`

### 6. after_stream retornava tipo errado (Streaming quebrado)
- **Arquivo**: `backend/app/chat/blueprint.py` + `chat/service.py`
- **Problema**: `_after_stream_agent()` retornava tupla (resposta, midia) mas blueprint tentava `resposta.id` na tupla
- **Solução**: Blueprint verifica `isinstance(after_result, tuple)` e desempacota

### 7. midia nunca chegava no frontend no streaming
- **Arquivo**: `backend/app/chat/service.py`
- **Problema**: `state.midia` lido no `return` antes do generator executar, sempre None
- **Solução**: `after_stream` retorna (resposta, midia), blueprint extrai do retorno

### 8. steps no agent_executor.stream() são tuplas, não dicts
- **Arquivo**: `backend/app/agents/service.py`
- **Problema**: Código tratava `step["steps"]` como dicts, mas são `(AgentAction, str_observation)`
- **Solução**: Verifica `isinstance(action_output, tuple)` e usa `action_output[1]`

### 9. Nginx + Cloudflare fazia buffer de SSE (streaming não funcionava via tunnel)
- **Arquivo**: `frontend/nginx.conf`
- **Problema**: proxy_buffering on, chunked_transfer_encoding off
- **Solução**: `proxy_buffering off`, `chunked_transfer_encoding on`, `add_header X-Accel-Buffering no`

### 10. Redirect URI do callback hardcoded
- **Arquivo**: `backend/app/auth/blueprint.py`
- **Problema**: FRONTEND_URL fixo como `http://127.0.0.1:8080`, não funcionava via Cloudflare Tunnel
- **Solução**: Detecta `X-Forwarded-Host` e `X-Forwarded-Proto` dos headers dinamicamente

## [04/06/2026] - Migração JWT + Correções Gerais

### 1. Autenticação das rotas Spotify
- **Arquivos**: `backend/app/spotify/blueprint.py`
- **Problema**: Rotas não estavam usando `@require_auth`, mantendo session antiga.
- **Solução**: Adicionado `@require_auth` em todas as rotas do blueprint.

### 2. getAuthenticatedUser no frontend
- **Arquivo**: `frontend/src/services/authService.ts`
- **Problema**: Usava fetch sem token, sessão antiga.
- **Solução**: Substituído por `authFetch` que injeta `Authorization: Bearer <jwt>`.

### 3. Profile.tsx com URLs e auth incorretos
- **Arquivo**: `frontend/src/pages/Profile.tsx`
- **Problema**: Usava `authFetch` com URLs erradas (sem `/api/spotify/profile`).
- **Solução**: Ajustado para usar `authFetch` + URLs corretas `/api/spotify/profile`.

### 4. get_mensagens_completas ausente no chat/repository
- **Arquivo**: `backend/app/chat/repository.py`
- **Problema**: Método `get_mensagens_completas` não existia, quebrava ao carregar histórico entre conversas.
- **Solução**: Adicionado método que retorna mensagens no formato esperado pelo frontend.

### 5. after_stream não chamado no blueprint
- **Arquivo**: `backend/app/chat/blueprint.py`
- **Problema**: O `after_stream()` não era chamado após o stream terminar, respostas não eram salvas.
- **Solução**: Implementado callback `after_stream()` no service + chamada no blueprint após consumir gerador.