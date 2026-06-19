# Arquitetura do MusicBot

## Diagrama de Fluxo
```
Frontend (React + Vite, Porta 8080)
    ↕ HTTP/JSON (JWT Bearer Token via authFetch)
Nginx (proxy reverso, desliga buffering SSE)
    ↕
Backend (Flask API + Gunicorn, Porta 5000)
    ↕ SQLAlchemy + pgvector
PostgreSQL (Docker pgvector/pgvector:pg16, Porta 5432)
    ↕
Serviços Externos:
├── Spotify API (OAuth2 + REST + Player API)
├── Ollama (LLM local, Porta 11434, GPU via nvidia driver)
├── IFES Colatina (LLM provider remoto alternativo, OpenAI-compatible API)
├── HuggingFace (Embeddings via Sentence Transformers)
├── ReccoBeats API (recomendação musical)
├── Wikipedia API (extração de artigos para base RAG)
└── SMTP/Gmail (envio de emails para recuperação de senha)

Serviços Internos (Flask Blueprints):
├── Auth (JWT + OAuth Spotify + Login custom + Recuperação de senha)
├── Chat (LangChain + RAG + Agents, streaming SSE)
├── Spotify API Client (perfil, playlists, músicas, playback)
├── Dashboard Analytics (estatísticas do usuário)
├── RAG Engine (embeddings, busca vetorial, chunking, síntese)
├── LangChain Agents (tool calling com Spotify, 16 tools)
├── LLM Provider (dual: local Ollama / remoto IFES)
├── MCP Server (13 tools via protocolo MCP, standalone)
└── Recommender Engine (ReccoBeats)

Ferramentas Auxiliares:
├── pgAdmin4 (Docker, Porta 5050, interface gráfica para PostgreSQL)
└── Cloudflare Tunnel (container com profile, link público trycloudflare.com)
```

## Módulos do Backend

### auth/
- Registro/login com email+senha + OAuth2 Spotify (PKCE)
- JWT via flask-jwt-extended
- Refresh automático do token Spotify
- PKCE state guard para callback
- Detecção de URL dinâmica (funciona com Cloudflare Tunnel)

### chat/
- Interface de chat com histórico e streaming SSE
- Detecção de intenção Spotify → delega para Agents
- RAG com síntese via create_stuff_documents_chain (LangChain)
- Fallback para LLM puro (Ollama)
- Memory do LangChain (DbChatMessageHistory com cache)
- Export de conversas (txt, json, md, pdf)
- Upload de arquivos (PDF, imagens, TXT, MD) com extração de texto
- Rota de feedback (POST /chat/feedback - like, dislike, report)

### spotify/
- Integração completa API Spotify (perfil, playlists, top tracks/artists, saved tracks, search)
- Playback real (play, pause, next, previous, fila)
- Dispositivos (listar, transferir, selecionar por nome)
- Pesquisa de artistas e top tracks
- Rotas protegidas por `@require_auth`
- Audio features via ReccoBeats

### rag/
- Retrieval-Augmented Generation para base de conhecimento musical
- Embeddings via Sentence Transformers (google/embeddinggemma-300m)
- Lazy loading thread-safe com Lock
- Chunking via RecursiveCharacterTextSplitter (LangChain)
- Busca vetorial com pgvector (distância cosseno)
- Fluxo de aprovação/rejeição de documentos
- Suporte a extração de URLs e PDFs
- Síntese via LangChain create_stuff_documents_chain

### agents/
- LangChain Agent Executor com tool calling
- 16 tools: busca, música recente, top músicas/artistas, curtidas, playlists, criar/adicionar playlist, buscar artista, tocar música/playlist, pausar, próximo/anterior, adicionar fila (1 ou lista), mudar dispositivo, listar dispositivos, criar playlist inteligente
- return_direct=True nas tools de execução (resposta direta sem LLM)
- Streaming via AgentExecutor.stream()
- max_iterations=5, handle_parsing_errors=True

### dashboard/
- Métricas e analytics do usuário
- Charts e feedbacks
- Reviews (like/dislike)

### reccobeats/
- Motor de recomendação musical via API externa
- Audio features integration

### llm_provider/
- Provider dual: local (Ollama) e remoto (IFES Colatina via OpenAI-compatible API)
- Toggle de provedor via endpoint `/api/llm-provider/toggle`
- Fallback automático: se provider não reconhecido, usa local
- Embeddings via Ollama local (`/api/embeddings`) ou IFES remoto

### langchain/
- Cliente Ollama unificado com configuração de stream
- Wrapper de streaming e resposta
- Build de mensagens LangChain a partir de histórico

### mcp_server.py
- Servidor MCP standalone (não roda dentro do Flask)
- 13 tools do Spotify expostas via protocolo MCP
- Para usar com Claude Desktop, Insomnia, etc.
- Token via env var SPOTIFY_ACCESS_TOKEN

### Serviços Auxiliares
- **pgAdmin4** — interface gráfica web para PostgreSQL (porta 5050)
- **Cloudflare Tunnel** — link público temporário via cloudflared (profile `tunnel`)
- **SMTP/Gmail** — envio de emails para recuperação de senha
- **Wikipedia** — script `dowloadWikipedia.py` para extração de artigos

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
3b. Se não → busca contexto RAG com síntese (RagSintese.consultar)
   3b1. Se contexto encontrado → resposta sintetizada via create_stuff_documents_chain
   3b2. Se não → prompt padrão do LLM
4. LLM gera resposta (streaming via Ollama)
5. Resposta salva no banco + fontes RAG salvas
6. Frontend exibe chunks em tempo real via SSE