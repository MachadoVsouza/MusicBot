# MusicBot - Visão Geral

## Descrição
Sistema de recomendação musical com chatbot inteligente, usando RAG (Retrieval-Augmented Generation) para consulta a base de conhecimento musical e LangChain Agents para interação com a API do Spotify em tempo real.

## Stack
- **Frontend**: React 18 + TypeScript 5.8 (strict) + Vite 7 + Tailwind CSS 3.4 + shadcn/ui (Radix UI) + react-markdown (remark-gfm)
- **Backend**: Python 3.12 + Flask 3 + SQLAlchemy 2 + LangChain 1.x + Gunicorn
- **Database**: PostgreSQL 16 com pgvector (via Docker) + pgAdmin4
- **LLM**: Ollama (gemma4:e4b) local com GPU + IFES Colatina (provider remoto alternativo)
- **IA/ML**: LangChain Agents (tool calling) + RAG (Sentence Transformers / Ollama Embeddings) + Spotify API
- **Auth**: JWT (flask-jwt-extended) + OAuth2 Spotify (PKCE) + Login custom (email/senha) + Recuperação de senha (SMTP/Gmail)
- **Containerização**: Docker Compose (db, ollama, ollama-init, backend, frontend, pgadmin, tunnel)

## Estrutura Principal
- `backend/` - API Flask com módulos organizados (auth, chat, spotify, rag, dashboard, agents, langchain, reccobeats, llm_provider)
- `frontend/` - SPA React com páginas de dashboard, chat, autenticação, perfil, base de conhecimento
- `docker-compose.yml` - Orquestração de 6 serviços (db, ollama, ollama-init, backend, frontend, pgadmin, tunnel via profile)
- `tunnel/` - Container Cloudflare Tunnel (cloudflared) para link público temporário
- `cline_docs/` - Memória do projeto (decisões, bugs, próximos passos, arquitetura, tecnologias)

## Funcionalidades Principais
- **Chat inteligente** com streaming SSE, detecção de intenção Spotify, RAG com síntese (create_stuff_documents_chain) e fallback para LLM puro
- **Integração Spotify** via langchain Agents (16 tools: busca, playlists, top tracks/artists, recentes, curtidas, playback, fila, dispositivos)
- **Base de conhecimento RAG** com upload de documentos (PDF, URLs, texto), chunking via LangChain, embeddings vetoriais (google/embeddinggemma-300m), busca vetorial com pgvector, fluxo de aprovação/rejeição de documentos
- **Playback real** via API REST player do Spotify (tocar, pausar, pular, fila, dispositivos) em vez de preview_url depreciado
- **Autenticação** JWT com suporte a OAuth2 Spotify e login custom (email/senha) com refresh automático de token
- **MCP Server** com 13 tools do Spotify expostas via protocolo MCP (Claude Desktop, Insomnia)
- **Memory do LangChain** com DbChatMessageHistory persistido no PostgreSQL
- **Dashboard** com métricas, analytics, tabelas de feedback/bugs paginadas (20 itens/página), auto-refresh 30s, exportação PDF/CSV/JSON
- **Export de conversas** em TXT, JSON, MD e PDF
- **Feedback inline** (like/dislike/report) por mensagem com toggle e DELETE, indicadores visuais
- **Markdown** nas respostas do bot com links customizados (badges com domínio visível, abertura em nova aba)
- **Dual provider LLM** (local Ollama / IFES Colatina) com toggle no chat

## Próximos Passos Prioritários
- Restringir LLM a não gerar links falsos/alucinados (playlists que não existem)
- Prune do modelo Ollama ou conectar com servidor IFES
- Sistema de recomendação (/v1/recommendations + ReccoBeats)
- Wikipedia automático no RAG