# Arquitetura do MusicBot

## Diagrama de Fluxo
```
Frontend (React + Vite, Porta 8080)
    ↕ HTTP/JSON (JWT Bearer Token via authFetch)
Nginx (proxy reverso)
    ↕
Backend (Flask API, Porta 5000)
    ↕ SQLAlchemy + pgvector
PostgreSQL (Docker, Porta 5432)
    ↕
Serviços Externos:
├── Spotify API (OAuth2 + REST)
├── Ollama (LLM local, Porta 11434)
├── HuggingFace (Embeddings via Sentence Transformers)
└── ReccoBeats API (recomendação musical)

Serviços Internos:
├── Auth (JWT + OAuth Spotify + Login custom)
├── Chat (LangChain + RAG + Agents)
├── Spotify API Client (perfil, playlists, músicas, artistas)
├── Dashboard Analytics (estatísticas do usuário)
├── RAG Engine (embeddings, busca vetorial, chunking)
├── LangChain Agents (tool calling com Spotify)
└── Recommender Engine (ReccoBeats)
```

## Módulos do Backend

### auth/
- Registro/login com email+senha + OAuth2 Spotify
- JWT via flask-jwt-extended
- Refresh automático do token Spotify
- PKCE state guard para callback

### chat/
- Interface de chat com histórico e streaming SSE
- Detecção de intenção Spotify → delega para Agents
- Fallback para RAG ou LLM puro
- Export de conversas (txt, json, md, pdf)
- Upload de arquivos (PDF, imagens, TXT, MD) com extração de texto

### spotify/
- Integração completa API Spotify (perfil, playlists, top tracks/artists, saved tracks, search)
- Rotas protegidas por `@require_auth`
- Audio features via ReccoBeats

### rag/
- Retrieval-Augmented Generation para base de conhecimento musical
- Embeddings via Sentence Transformers (google/embeddinggemma-300m)
- Chunking via RecursiveCharacterTextSplitter (LangChain)
- Busca vetorial com pgvector (distância cosseno)
- Fluxo de aprovação/rejeição de documentos
- Suporte a extração de URLs e PDFs

### agents/
- LangChain Agent Executor com tool calling
- Tools: buscar música, música recente, top músicas/artistas, curtidas, playlists, criar/adicionar playlist, buscar artista
- max_iterations=5, handle_parsing_errors=True
- Retorno de midia (preview_url) para o frontend

### dashboard/
- Métricas e analytics do usuário
- Charts e feedbacks

### reccobeats/
- Motor de recomendação musical via API externa
- Audio features integration

### langchain/
- Cliente Ollama unificado com configuração de stream
- Wrapper de streaming e resposta
- Build de mensagens LangChain a partir de histórico

## Padrões
- Repository Pattern para acesso a dados
- Blueprint Pattern (Flask blueprints)
- Service Layer para lógica de negócio
- JWT stateless authentication
- SSE (Server-Sent Events) para streaming de respostas

## Pipeline de Requisição do Chat
```
1. Frontend envia mensagem → /chat/<id>/stream (SSE)
2. ChatService detecta intenção Spotify via regex
3a. Se intenção Spotify → run_agent (LangChain Agent + Spotify tools)
3b. Se não → busca contexto RAG (buscar_similares)
   3b1. Se contexto encontrado → prompt RAG + chunks
   3b2. Se não → prompt padrão
4. LLM gera resposta (streaming)
5. Resposta salva no banco + fontes RAG salvas
6. Frontend exibe chunks em tempo real via SSE