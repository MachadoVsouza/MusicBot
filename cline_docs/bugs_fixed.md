# Bugs Corrigidos

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

---

*Histórico de bugs corrigidos será mantido aqui.*