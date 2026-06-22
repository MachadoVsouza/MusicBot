# Bugs Corrigidos — MusicBot

## [21/06/2026] — Fases 1-3: Feedback, Dashboard e Links

### Fase 1 — Feedback Inline, Toggle e DELETE
- **Botões feedback no rodapé (sempre última mensagem)**: `conversationRating` era estado único, sempre afetava a última resposta do bot independente de qual foi clicada
  - **Solução**: Substituído por `feedbackState: Record<number, FeedbackEntry>` mapeado por `respostaId`. Botões 👍/👎 movidos para dentro de cada balão de resposta (`inline`)
  - **Arquivo**: `frontend/src/pages/Chat.tsx`
- **Toggle de feedback (remover like/dislike)**: Clicar 👍 quando já tinha like não removia do backend
  - **Solução**: Adicionado `DELETE /chat/feedback/<id>` no backend (`blueprint.py`) com validação de propriedade. Frontend faz DELETE quando mesmo tipo é clicado novamente, ou DELETE+POST quando troca like↔dislike
  - **Arquivos**: `backend/app/chat/blueprint.py`, `frontend/src/pages/Chat.tsx`
- **Dislike sem toast**: Só like e report tinham toast de confirmação
  - **Solução**: Adicionado toast "Dislike registrado" e toast "Feedback removido"
- **respostaId ausente sem aviso**: Se SSE falhasse ao salvar, sendFeedback retornava silenciosamente
  - **Solução**: sendReport mostra toast de erro "Nenhuma resposta disponível para reportar"
- **Indicador visual de feedback**: Não havia indicação se uma mensagem já tinha feedback
  - **Solução**: Badge "👍 Obrigado!" (verde) ou "👎 Feedback registrado" (vermelho) abaixo dos botões

### Fase 2 — Dashboard: Paginação, Auto-Refresh e Limite 20
- **Dashboard sem paginação**: LIMIT 100 em todas as queries, sem parâmetros de página
  - **Solução**: Adicionado `page`/`per_page` com OFFSET no repository, service e blueprint. LIMIT reduzido para 20. Retorno padronizado como `{items, total, page, per_page, total_pages}`
  - **Arquivos**: `backend/app/dashboard/repository.py`, `service.py`, `blueprint.py`
- **Sem auto-refresh**: Dados só atualizavam ao trocar período
  - **Solução**: `setInterval(load, 30_000)` no `useDashboard` hook com cleanup no unmount
  - **Arquivo**: `frontend/src/hooks/useDashboard.ts`
- **Sem indicador de refresh**: Usuário não sabia quando os dados foram atualizados
  - **Solução**: Botão "Atualizar" manual + label "Última atualização: HH:MM:SS (auto: 30s)"
  - **Arquivo**: `frontend/src/pages/Dashboard.tsx`
- **Controles de paginação**: Sem navegação entre páginas nas tabelas
  - **Solução**: Componente `PaginationControls` com ← 1 2 3 ... → em cada tabela
  - **Arquivo**: `frontend/src/pages/Dashboard.tsx`

### Fase 3 — Enriquecimento de Dados e Unificação
- **Tabelas Feedbacks e Avaliações redundantes**: Duas tabelas mostrando os mesmos dados com colunas diferentes
  - **Solução**: Unificadas em uma única tabela "Feedbacks dos Usuários" com colunas: Tipo, Usuário, Conversa, Mensagem Avaliada, Data
  - **Arquivos**: `frontend/src/pages/Dashboard.tsx`, `frontend/src/types/index.ts`, `frontend/src/hooks/useDashboard.ts`
- **usuario_id cru no Dashboard**: Tabela de avaliações mostrava Spotify ID (hash) em vez de email
  - **Solução**: JOIN com `Usuario` em `get_feedbacks`, `get_bugs`, `get_avaliacoes`. Exibe `usuario_email`
  - **Arquivo**: `backend/app/dashboard/repository.py`
- **Coluna Mensagem Avaliada ausente**: Dashboard não mostrava o conteúdo da resposta que recebeu feedback
  - **Solução**: JOIN com `Resposta` em `get_feedbacks`, incluindo `resposta.conteudo[:200]` como `mensagem_avaliada`
  - **Arquivo**: `backend/app/dashboard/repository.py`
- **Toggle de ordenação**: Sem controle de ordem nas tabelas
  - **Solução**: Parâmetro `order_by: "id" | "created_at"` no backend e toggle 🆔 ID / 📅 Data no frontend
- **exportRelatorio sem authFetch**: Usava `fetch` puro com `localStorage.getItem('musicbot_jwt')` manual
  - **Solução**: Substituído por `authFetch` consistente com o resto do código
  - **Arquivo**: `frontend/src/services/dashboardService.ts`
- **Tipos removidos**: `DashboardReview`, `ReviewRating`, `type ReviewFilter` removidos após unificação
  - **Arquivo**: `frontend/src/types/index.ts`

### Bug Crítico — Botões desapareciam ao recarregar conversa
- **Camada 1 — Repository não retornava resposta_id**: `get_mensagens_completas` não incluía `resposta_id` no retorno
  - **Solução**: Adicionado `"resposta_id": p.resposta.id` e `"pergunta_id": p.id` no dicionário
  - **Arquivo**: `backend/app/chat/repository.py`
- **Camada 2 — Service descartava metadados**: `get_mensagens` mapeava apenas `{id, role, content, timestamp}`, jogando fora `resposta_id`
  - **Solução**: Adicionado `"resposta_id": m.get("resposta_id")`, `"pergunta_id": m.get("pergunta_id")`, `"usou_rag": m.get("usou_rag")`
  - **Arquivo**: `backend/app/chat/service.py`
- **Camada 3 — Role mismatch**: `get_mensagens_completas` retornava `role: "assistant"` mas frontend espera `role: "bot"`
  - **Solução**: Alterado para `"role": "bot"` (apenas em `get_mensagens_completas`; `get_historico` mantém `"assistant"` para o LLM)
  - **Arquivo**: `backend/app/chat/repository.py`

### Links e Markdown
- **Links quebrados sem https://**: LLM gerava `[open.spotify.com/...](open.spotify.com/...)` sem protocolo
  - **Solução**: `MarkdownRenderer` prefixa `https://` automaticamente quando URL não tem protocolo
  - **Arquivo**: `frontend/src/pages/Chat.tsx`
- **Links brutos ilegíveis**: `[https://url.longa](https://url.longa)` aparecia como texto markdown
  - **Solução**: `react-markdown` + `remark-gfm` com componente `<a>` customizado: badge verde com ícone 🔗, domínio extraído, abre em nova aba
  - **Arquivo**: `frontend/src/pages/Chat.tsx`

### Prompt — Restrição de Plataformas
- **Bot recomendava Deezer, Apple Music**: SYSTEM_PROMPT não tinha restrição
  - **Solução**: Adicionada seção "Plataformas" proibindo mencionar concorrentes do Spotify
  - **Arquivo**: `backend/app/chat/service.py`

---

## [15/06/2026] — Fases 1-8: Refatoração Completa do Frontend

### Fase 1 — Configuração
- **Favicon quebrado**: `href="/frontend/public/green-icon-music-bot.svg"` → corrigido para `href="/green-icon-music-bot.svg"`
- **Lang errado**: `lang="en"` → `lang="pt-BR"`
- **Nome do projeto**: `"vite_react_shadcn_ts"` → `"musicbot"` no `package.json`
- **HMR overlay desabilitado**: `overlay: false` removido do `vite.config.ts`
- **ESLint**: `no-unused-vars: "off"` → `"warn"`

### Fase 2 — Bugs
- **Typo CSS**: `bg-greentext-off-white` (falta espaço) → `bg-green text-off-white` no `RegistrationForm.tsx`
- **Redirecionamento errado**: Botão "Entrar" no Cadastro ia para `/under-construction` → `/chat`
- **404 em inglês**: "Oops! Page not found" → "Página não encontrada"
- **Código morto**: Bloco comentado (perfil fake João Silva) removido do `Cadastro.tsx`
- **RecuperarSenha fake**: `handleSubmit` só fazia `setSent(true)` sem chamar API → implementada funcionalidade completa (JWT + SMTP)

### Fase 3 — TypeScript Strict Mode
- **7 erros de tipagem** corrigidos em 5 arquivos:
  - `AuthContext.tsx`: `React` import não usado
  - `Cadastro.tsx`: `useEffect` import não usado
  - `Entrar.tsx`: `handleSpotifyLogin` função não usada, `redirectToSpotifyAuth` import não usado
  - `Profile.tsx`: `devices` e `onSelectDevice` props não usadas no `PlayOnSpotify`
  - `authService.ts`: variável `profile` não usada
  - `Chat.tsx`: `any[]` implícito no map → adicionado `: Conversation`

### Fase 4 — Padronização
- **Imports inconsistentes**: 4 arquivos com `'../'` → padronizados para `@/`
- **Toast duplicado**: `Sonner` + `shadcn/ui toast` coexistindo → removido Sonner
- **Fontes divergentes**: `Syne`/`DM Sans`/`JetBrains Mono` no config vs `Figtree` no CSS → unificado para Figtree
- **App.css boilerplate**: Código Vite nunca usado (`.logo`, `.card`, `logo-spin`) → arquivo deletado

### Fase 5 — Tipos Centralizados
- **Tipos duplicados**: `UserProfile` em 2 arquivos, `Message`/`Conversation`/etc no Chat.tsx, `DashboardMetrics`/etc no dashboardService.ts → todos movidos para `src/types/index.ts`
- **7 arquivos** atualizados para importar de `@/types`

### Fase 6 — Decomposição
- **Chat.tsx monolítico**: 647 linhas com MiniPlayer, modais, toggle, export tudo no mesmo arquivo → decomposto em 6 componentes
- **PlayOnSpotify inline**: Extraído de `Profile.tsx` para `src/components/chat/PlayOnSpotify.tsx`
- **Keyframes inline**: `wave`, `pulse`, `scrollAnim`, `glowAnim` injetados via `<style>` em `Profile.tsx` → movidos para `index.css`

### Recuperação de Senha
- **Erro 500**: `create_access_token(expires_delta=3600)` → `timedelta(hours=1)` (parâmetro espera `timedelta`, não `int`)
- **Erro 502**: Container backend recriado com novo IP, nginx com cache do IP antigo → `docker compose restart frontend`

### Fase 7 — UX
- **Mensagens sem formatação**: `<p className="whitespace-pre-wrap">` → `<ReactMarkdown>` com suporte a negrito, código, listas, links
- **Preferências não persistidas**: `audioEnabled`/`compactMode` perdiam ao recarregar → salvas em `localStorage` (`musicbot_prefs`)
- **Deletar sem confirmação**: Exclusão de documento silenciosa → `window.confirm()` antes de deletar

### Fase 8 — Performance
- **Componentes sem memo**: `MusicbotLogo`, `AuthCard`, `MetricCard`, `EmptyTableRow` → `React.memo()` adicionado com `displayName`

---

## [07/06/2026] — Sessão 3: User Roles, OAuth Session, Login Custom

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

### pgAdmin4 adicionado ao docker-compose
- Serviço `pgadmin` (dpage/pgadmin4) na porta `5050` com volume persistente

## [06/06/2026] — Sessão: Correção de Login

### Redirect URI errada no docker-compose.yml
- **Arquivo**: `docker-compose.yml`
- **Problema**: `SPOTIFY_REDIRECT_URI` estava `http://127.0.0.1:8080/auth/callback` (faltando `/api/`)
- **Consequência**: Spotify redirecionava para `/auth/callback`, que não batia com o `location /api/` do nginx
- **Correção**: Alterado para `http://127.0.0.1:8080/api/auth/callback`

### Coluna llm_provider inexistente no banco
- **Arquivo**: `backend/app/database/models.py`
- **Problema**: O modelo definia a coluna `llm_provider` mas a tabela no PostgreSQL não tinha
- **Erro**: `psycopg2.errors.UndefinedColumn: column usuario.llm_provider does not exist`
- **Correção**: Banco recriado com `docker compose down -v && docker compose up --build -d`

---

## [05/06/2026] — Sessão 2: Playback, Streaming e JWT

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

## [04/06/2026] — Migração JWT + Correções Gerais

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