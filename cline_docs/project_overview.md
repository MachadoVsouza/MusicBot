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
- **Containerização**: Docker Compose (db, ollama, backend, frontend + init)

## Estrutura Principal
- `backend/` - API Flask com módulos organizados (auth, chat, spotify, rag, dashboard, agents, langchain, reccobeats)
- `frontend/` - SPA React com páginas de dashboard, chat, autenticação, perfil, base de conhecimento
- `docker-compose.yml` - Orquestração dos serviços (db, ollama, ollama-init, backend, frontend)

## Funcionalidades Principais
- **Chat inteligente** com streaming SSE, detecção de intenção Spotify, RAG e fallback para LLM puro
- **Integração Spotify** via langchain Agents (buscar música, playlists, top tracks/artists, recentes, curtidas, criar/adicionar playlist, buscar artista)
- **Base de conhecimento RAG** com upload de documentos (PDF, URLs, texto), chunking via LangChain, embeddings vetoriais, busca por similaridade, fluxo de aprovação/rejeição
- **Autenticação** JWT com suporte a OAuth2 Spotify e login custom (email/senha) com refresh automático de token
- **Dashboard** com métricas e analytics do usuário
- **Export de conversas** em TXT, JSON, MD e PDF
- **Pré-visualização de música** com Mini Player (30s preview do Spotify)

## Próximos Passos
- Cloudflare Tunnel para compartilhamento público
- MCP Server para expor tools do Spotify
- RAG com síntese (RetrievalQA do LangChain)
- Memory do LangChain (RunnableWithMessageHistory)
- Streaming real do agent