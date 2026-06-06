# MusicBot - Visão Geral

## Descrição
Sistema de recomendação musical com chatbot inteligente, usando RAG (Retrieval-Augmented Generation) para consulta a base de conhecimento musical e LangChain Agents para interação com a API do Spotify em tempo real.

## Stack
- **Frontend**: React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: Python + Flask + SQLAlchemy + LangChain
- **Database**: PostgreSQL com pgvector (via Docker)
- **LLM**: Ollama (gemma4:e4b) local com GPU
- **IA/ML**: LangChain + Agents + RAG (Sentence Transformers) + Spotify API
- **Auth**: JWT (flask-jwt-extended) + OAuth2 Spotify + Login custom (email/senha)
- **Containerização**: Docker Compose (db, ollama, backend, frontend, tunnel)

## Estrutura Principal
- `backend/` - API Flask com módulos organizados (auth, chat, spotify, rag, dashboard, agents, langchain, reccobeats)
- `frontend/` - SPA React com páginas de dashboard, chat, autenticação, perfil, base de conhecimento
- `docker-compose.yml` - Orquestração dos serviços (db, ollama, ollama-init, backend, frontend, tunnel)
- `tunnel/` - Container Cloudflare Tunnel para link público temporário
- `cline_docs/` - Memória do projeto (decisões, bugs, próximos passos)

## Funcionalidades Principais
- **Chat inteligente** com streaming SSE, detecção de intenção Spotify, RAG com síntese (create_stuff_documents_chain) e fallback para LLM puro
- **Integração Spotify** via langchain Agents (16 tools: busca, playlists, top tracks/artists, recentes, curtidas, playback, fila, dispositivos)
- **Base de conhecimento RAG** com upload de documentos (PDF, URLs, texto), chunking via LangChain, embeddings vetoriais (google/embeddinggemma-300m), busca vetorial com pgvector, fluxo de aprovação/rejeição de documentos
- **Playback real** via API REST player do Spotify (tocar, pausar, pular, fila, dispositivos) em vez de preview_url depreciado
- **Autenticação** JWT com suporte a OAuth2 Spotify e login custom (email/senha) com refresh automático de token
- **MCP Server** com 13 tools do Spotify expostas via protocolo MCP (Claude Desktop, Insomnia)
- **Memory do LangChain** com DbChatMessageHistory persistido no PostgreSQL
- **Dashboard** com métricas e analytics do usuário
- **Export de conversas** em TXT, JSON, MD e PDF

## Próximos Passos Prioritários
- Conectar feedback (like/dislike/report) do Chat.tsx ao backend
- Prune do modelo Ollama ou conectar com servidor IFES
- Sistema de recomendação (/v1/recommendations + ReccoBeats)
- Wikipedia automático no RAG