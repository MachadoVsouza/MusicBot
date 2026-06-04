# Checklist de Segurança

## Autenticação
- [x] JWT com flask-jwt-extended (migrado de Flask-Session)
- [ ] Refresh token rotation (token Spotify renova, JWT não tem refresh)
- [ ] Rate limiting em rotas de login/cadastro
- [x] Validação de força de senha (mínimo 6 caracteres)

## API
- [ ] CORS configurado corretamente
- [ ] Input sanitization em todas as rotas
- [ ] Rate limiting em endpoints públicos
- [x] Validação de tokens expirados (flask-jwt-extended)

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