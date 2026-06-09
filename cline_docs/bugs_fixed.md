# Bugs Corrigidos

## [08/06/2026] - Sessão 4: SuperUsuario, Dashboard, Audit Log

### 15. Usuário sem acesso a Dashboard/Base de Conhecimento (403 Forbidden)
- **Arquivos**: `backend/app/auth/service.py`, `backend/app/__init__.py`, `backend/app/auth/blueprint.py`, `backend/app/core/auth_guard.py`, `backend/app/config.py`
- **Problema**: Spotify ID real do usuário (`eyt6axvep2ar2p7rpzjk2j0mv`) não estava na lista `SUPER_USER_IDS`. O login por email/senha nunca criava o registro `SuperUsuario`/`Moderador` no banco porque `_verificar_e_criar_super_usuario()` só era chamado no callback OAuth. O `from_object()` do Flask não copiava a lista `SUPER_USER_IDS` corretamente.
- **Solução**: 
  - `login_with_password()` agora chama `_verificar_e_criar_super_usuario()` para IDs fixos
  - `create_app()` injeta `SUPER_USER_IDS` explicitamente com `app.config["SUPER_USER_IDS"] = list(super_ids)`
  - Registros `super_usuario` e `moderador` populados diretamente via SQL para correção imediata
  - ID real do usuário adicionado à lista `SUPER_USER_IDS`
- **Impacto**: Botões Dashboard/Base de Conhecimento não apareciam e endpoints retornavam 403.

### 16. Botão "Exportar relatório" no Dashboard sem ação
- **Arquivos**: `frontend/src/pages/Dashboard.tsx`, `frontend/src/services/dashboardService.ts`, `backend/app/dashboard/blueprint.py`
- **Problema**: Botão "Exportar relatório" era um `<button>` sem `onClick` — clicar não fazia nada.
- **Solução**: 
  - Novo endpoint `GET /dashboard/export?period=...&format=pdf|csv` com PDF via reportlab e CSV via csv.writer
  - Dropdown com opções PDF/CSV, função `exportRelatorio()` no service e handler `onClick` no componente
- **Impacto**: Requisito 2.5 do PDF ("relatórios de desempenho") agora parcialmente atendido.

### 17. Erro 500 no streaming do chat (OOM Killer)
- **Arquivos**: Diagnóstico apenas, sem alteração de código
- **Problema**: Worker do gunicorn sendo morto com SIGKILL pelo kernel Linux por falta de memória (OOM Killer). O modelo Ollama (`qwen:4b`) consumia RAM excessiva no mesmo host Docker.
- **Solução**: Usar o provider IFES (workstations externas) que não consome RAM local.
- **Impacto**: Chat quebrava com 500 ao tentar gerar respostas longas.

---

## [07/06/2026] - Sessão 3: User Roles, OAuth Session, Login Custom

### 14. SuperUsuários fixos não funcionavam (IDs de desenvolvedor sem role moderador)
- **Arquivos**: `backend/app/config.py`, `backend/app/auth/service.py`, `backend/app/auth/repository.py`, `backend/app/auth/blueprint.py`
- **Problema**: Código anterior só criava SuperUsuario para `type: "artist"` do Spotify. Os IDs `818da73b30404df29b817237bd1a936c` e `b5727e21ded847928278e6fe1782060f` nunca recebiam role de moderador, e os botões Dashboard/Base não apareciam.
- **Solução**: Lista `SUPER_USER_IDS` no config; `_verificar_e_criar_super_usuario()` aceita IDs fixos OU artistas; `register_user()` salva perfil na sessão para verificação pós-registro; `/me` com fallback `garantir_super_usuario_para_id_fixo()` que cria SuperUsuario/Moderador no banco automaticamente.
- **Impacto**: Sem o fix, os perfis de desenvolvedor eram tratados como usuários comuns, sem acesso ao Dashboard e Base de Conhecimento.

### 11. Sessão Flask inválida no callback OAuth (state_invalido)
- **Arquivos**: `backend/app/config.py`, `frontend/nginx.conf`
- **Problema**: `SESSION_COOKIE_SAMESITE="None"` com `SESSION_COOKIE_SECURE=False` (HTTP) é inválido no Chrome — cookie rejeitado. Além disso, nginx não repassava `Set-Cookie` do backend.
- **Solução**: `SameSite="Lax"` (permite GET cross-site), `proxy_pass_header Set-Cookie`, `proxy_cookie_path / /`, `X-Forwarded-Host $http_host`
- **Impacto**: Login com Spotify quebrava 100% das vezes com erro `state_invalido`

### 12. Login com email/senha não carregava perfil corretamente
- **Arquivo**: `frontend/src/pages/Entrar.tsx`
- **Problema**: Usava `loginWithProfile` (fluxo do callback Spotify) em vez de `loginWithToken` (fluxo de login custom). Manipulava localStorage e perfil Spotify manualmente, sem passar pelo AuthContext.
- **Solução**: Substituído `loginWithProfile` por `loginWithToken` — que valida JWT, obtém role/super_usuario_id e carrega perfil Spotify automaticamente
- **Impacto**: Login com email/senha não populava o contexto de usuário, redirecionava sem perfil

### 13. super_usuario_id hardcoded no BaseConhecimento.tsx
- **Arquivo**: `frontend/src/pages/BaseConhecimento.tsx`
- **Problema**: `super_usuario_id: 1` fixo no submit de documentos. Se não existir SuperUsuario com ID 1 no banco, falha.
- **Solução**: Usa `user.superUsuarioId` do AuthContext (obtido via `/api/auth/me`)

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