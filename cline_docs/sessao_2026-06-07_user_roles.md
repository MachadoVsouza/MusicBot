# Sessão 07/06/2026 — User Roles (Usuário Comum vs Super Usuário) + Correções

## O que foi implementado

### 1. Distinção Usuário Comum vs Super Usuário (Artista Spotify)
- **Backend**: Detecção automática do tipo de conta Spotify (`type: "artist"` vs `type: "user"`)
  - `handle_spotify_callback()` verifica o campo `type` do perfil `/v1/me`
  - Se `type === "artist"`, cria automaticamente `SuperUsuario` + vincula como `Moderador` administrador
  - `auth/repository.py`: adicionados `get_moderador_by_usuario_id()` e `criar_super_usuario_e_moderador()`
- **Endpoint `/api/auth/me`** agora retorna `role` (`"user"` | `"moderator"`) e `super_usuario_id`
- **Frontend `AuthContext`**: novo campo `superUsuarioId` e helper `isModerator`
- **Proteção de telas**:
  - `Dashboard.tsx`: tela "Acesso Restrito" para usuários comuns
  - `BaseConhecimento.tsx`: tela "Acesso Restrito" + `super_usuario_id` dinâmico (removido hardcoded `1`)
  - `Chat.tsx`: links Dashboard/Base ocultos no menu settings para usuários comuns
- **Moderadores fixos**: IDs `818da73b30404df29b817237bd1a936c` e `b5727e21ded847928278e6fe1782060f` como moderadores permanentes (`FIXED_MODERATOR_IDS` no config)

### 2. Correção do Bug `state_invalido` (OAuth PKCE)
- **Causa**: Sessão Flask perdia cookies de sessão devido a `SameSite=None` com `Secure=False` (inválido no Chrome) + nginx não repassava `Set-Cookie`
- **Correções**:
  - `nginx.conf`: adicionado `proxy_pass_header Set-Cookie`, `proxy_cookie_path / /`, `X-Forwarded-Host $http_host`
  - `config.py`: `SESSION_COOKIE_SAMESITE` ajustado para `"Lax"` (permite GET cross-site redirect)
- O fluxo OAuth agora funciona consistentemente: `GET /api/auth/login` → Spotify → `GET /api/auth/callback` sem perder estado

### 3. Correção do Login com Email/Senha
- **Bug**: `Entrar.tsx` usava `loginWithProfile` (fluxo do callback Spotify) em vez de `loginWithToken`
- **Correção**: Substituído `loginWithProfile` por `loginWithToken` — que valida JWT, obtém `role`/`super_usuario_id` e carrega perfil Spotify automaticamente

## Arquivos Modificados

### Backend (4 arquivos)
| Arquivo | Mudança |
|---------|---------|
| `backend/app/config.py` | `SESSION_COOKIE_SAMESITE="Lax"`, `FIXED_MODERATOR_IDS` |
| `backend/app/auth/repository.py` | `get_moderador_by_usuario_id()`, `criar_super_usuario_e_moderador()` |
| `backend/app/auth/service.py` | `_verificar_e_criar_super_usuario()` — detecção de artista Spotify |
| `backend/app/auth/blueprint.py` | `/api/auth/me` retorna `role` + `super_usuario_id`; verifica `FIXED_MODERATOR_IDS` |

### Frontend (6 arquivos)
| Arquivo | Mudança |
|---------|---------|
| `frontend/src/contexts/AuthContext.tsx` | `superUsuarioId`, `isModerator`, `fetchMeData()` |
| `frontend/src/pages/BaseConhecimento.tsx` | Remove `super_usuario_id: 1` hardcoded; tela acesso restrito; usa `useAuth()` |
| `frontend/src/pages/Dashboard.tsx` | Tela "Acesso Restrito" para `!isModerator` |
| `frontend/src/pages/Chat.tsx` | Links Dashboard/Base condicionados a `isModerator` |
| `frontend/src/pages/Entrar.tsx` | `loginWithProfile` → `loginWithToken` |
| `frontend/nginx.conf` | `proxy_pass_header Set-Cookie`, `X-Forwarded-Host $http_host`, `proxy_cookie_path` |

## Próximos Passos
- [x] Testar login Spotify (funcionando)
- [x] Testar login email/senha (funcionando)
- [ ] Testar com conta artista Spotify real para validar auto-detecção
- [ ] Verificar se `b5727e21ded847928278e6fe1782060f` é realmente um `spotify_id` (pode ser `client_id` duplicado)