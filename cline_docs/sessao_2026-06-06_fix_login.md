# Sessão 06/06/2026 — Correção do Bug de Login

## Problema
O novo colaborador do projeto não conseguia fazer login via Spotify. Após autorizar no Spotify, o frontend exibia erro de autenticação e redirecionava para `/entrar?error=auth_failed`. O colaborador antigo conseguia usar normalmente.

## Bugs Corrigidos

### 1. Redirect URI errada no `docker-compose.yml`
- **Arquivo**: `docker-compose.yml` (linha 74)
- **Problema**: `SPOTIFY_REDIRECT_URI` estava `http://127.0.0.1:8080/auth/callback` (faltando `/api/`)
- **Consequência**: Spotify redirecionava para `/auth/callback`, que não batia com o `location /api/` do nginx. O nginx servia o SPA em vez de proxy para o backend. O componente `AuthCallback` recebia `?code=...&state=...` na URL em vez de `?token=...`.
- **Correção**: Alterado para `http://127.0.0.1:8080/api/auth/callback`

### 2. Coluna `llm_provider` inexistente no banco
- **Arquivo**: `backend/app/database/models.py` (linha 36)
- **Problema**: O modelo SQLAlchemy definia a coluna `llm_provider` no `Usuario`, mas a tabela no PostgreSQL não tinha essa coluna (banco foi criado antes da adição do campo).
- **Erro**: `psycopg2.errors.UndefinedColumn: column usuario.llm_provider does not exist`
- **Correção**: Banco recriado com `docker compose down -v && docker compose up --build -d`

## O que foi feito
1. Analisado o fluxo completo de autenticação (Spotify → nginx → Flask → callback → JWT → frontend)
2. Identificado o `SPOTIFY_REDIRECT_URI` incorreto no `docker-compose.yml`
3. Aplicada correção da URI
4. Identificado o erro 500 por schema mismatch do banco
5. Recriado o banco (com perda de dados de desenvolvimento)

## Próximos Passos
- [ ] Testar login com Spotify e confirmar fluxo completo (autorizar → formulário cadastro → chat)
- [ ] Verificar criação de playlists e playback real no Spotify
- [ ] Testar upload de documentos na base RAG
- [ ] Avaliar migração do Ollama para servidor IFES Colatina (já configurado)
- [ ] Implementar rate limiting nas rotas de login (ver `security_checklist.md`)
- [ ] Testar Cloudflare Tunnel (`docker compose --profile tunnel up`)