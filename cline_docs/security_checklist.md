# Checklist de Segurança

## Autenticação
- [x] JWT com flask-jwt-extended (migrado de Flask-Session)
- [ ] Refresh token rotation (token Spotify renova, JWT não tem refresh)
- [ ] Rate limiting em rotas de login/cadastro
- [x] Validação de força de senha (mínimo 6 caracteres)
- [x] Sessão Flask: SameSite=Lax + nginx proxy_pass_header Set-Cookie
- [x] Role-based access: `/api/auth/me` retorna role + super_usuario_id
- [x] Proteção de Dashboard e Base de Conhecimento (só moderadores)
- [ ] `_is_token_valid()` faz GET /v1/me a cada requisição (consome rate limit Spotify)

## API
- [ ] CORS configurado corretamente
- [ ] Input sanitization em todas as rotas
- [ ] Rate limiting em endpoints públicos
- [x] Validação de tokens expirados (flask-jwt-extended)
- [x] Rotas protegidas por `@require_auth`

## Chat/RAG
- [ ] Sanitização de input do usuário
- [ ] Proteção contra prompt injection
- [ ] Logs sem dados sensíveis
- [x] Limite de tokens por requisição (num_predict=2048)

## Dados
- [x] Senhas hasheadas (bcrypt no service layer)
- [ ] Conexão SSL/TLS com banco
- [x] Variáveis de ambiente para secrets (JWT_SECRET_KEY, SPOTIFY_CLIENT_SECRET, HUGGINGFACE_TOKEN)
- [x] .env nunca versionado

## Frontend
- [x] Validação de formulários client-side
- [x] Token JWT armazenado em localStorage
- [ ] Refresh token automático (token Spotify renova pelo backend, JWT não)
- [ ] Logout em inatividade

## RAG
- [x] Embeddings normalizados (normalize_embeddings=True)
- [x] Verificação de duplicata via similaridade vetorial (threshold 0.15)
- [x] Batch processing com rollback em caso de erro
- [x] Lazy loading thread-safe com Lock
- [ ] Sanitização de conteúdo de URLs/PDFs extraídos

## MCP Server
- [ ] Token fixo via env var (expira em 1h, sem refresh)
- [ ] Não roda autenticado dentro do mesmo contexto que o Flask

## Cloudflare Tunnel
- [x] Container isolado com profile (só roda quando explicitamente iniciado)
- [ ] Redirect URI precisa ser adicionado manualmente no Dashboard do Spotify
- [ ] Link público expira quando container morre