# Tecnologias do MusicBot

Documento detalhado de todas as tecnologias, bibliotecas, frameworks e serviços utilizados no projeto MusicBot — chatbot inteligente de recomendação musical.

---

## 1. Backend Core

### Python 3.12
- **Propósito**: Linguagem principal do backend.
- **Uso**: Toda a API REST, lógica de negócio, agentes LangChain e integrações são escritas em Python.
- **Por que 3.12**: Versão estável mais recente com suporte a melhorias de performance e sintaxe moderna.

### Flask 3.x
- **Propósito**: Micro-framework web para construção da API REST.
- **Uso**: Servidor HTTP que expõe todas as rotas do backend (auth, chat, spotify, rag, dashboard, llm_provider).
- **Padrão**: Blueprint Pattern — cada módulo é um Flask Blueprint registrado no `run.py`.
- **Pacote**: `flask>=3.0`

### Gunicorn
- **Propósito**: Servidor WSGI de produção que substitui o servidor de desenvolvimento do Flask.
- **Uso**: Definido no `Dockerfile` do backend: `gunicorn run:app --bind 0.0.0.0:5000 --workers 2 --timeout 120 --keep-alive 5`
- **Configuração**: 2 workers para paralelismo leve, timeout de 120s para requisições longas (chat streaming), keep-alive de 5s.
- **Pacote**: `gunicorn`

---

## 2. Banco de Dados & ORM

### PostgreSQL 16
- **Propósito**: Banco de dados relacional principal.
- **Uso**: Armazena usuários, conversas, documentos RAG, embeddings vetoriais, tokens Spotify, métricas do dashboard.
- **Container**: `pgvector/pgvector:pg16` (imagem oficial do PostgreSQL 16 com extensão pgvector pré-instalada).

### pgvector
- **Propósito**: Extensão do PostgreSQL para busca vetorial (similaridade de embeddings).
- **Uso**: Armazena embeddings gerados pelo modelo de linguagem na tabela `fragmento` e permite busca por distância cosseno (`<=>`).
- **Índice**: IVFFlat com `lists=100` para aceleração de queries.
- **Pacote Python**: `pgvector>=0.3`

### SQLAlchemy 2.x
- **Propósito**: ORM (Object-Relational Mapping) para interagir com o PostgreSQL.
- **Uso**: Define modelos Python (`backend/app/database/models.py`) que mapeiam para tabelas. Usa `mapped_column` e `Mapped[]` (sintaxe 2.x).
- **Pacote**: `sqlalchemy>=2.0`

### psycopg2-binary
- **Propósito**: Driver PostgreSQL nativo para Python.
- **Uso**: Conector de baixo nível usado pelo SQLAlchemy para comunicação com o banco.
- **Pacote**: `psycopg2-binary>=2.9`

### pgAdmin4
- **Propósito**: Interface gráfica web para administração do PostgreSQL.
- **Uso**: Serviço Docker auxiliar exposto na porta `5050`. Acesso via `admin@musicbot.com` / `admin`.
- **Container**: `dpage/pgadmin4:latest`

---

## 3. Inteligência Artificial / LLM

### Ollama
- **Propósito**: Servidor local de LLMs (Large Language Models) com aceleração GPU.
- **Uso**: Executa o modelo `gemma4:e4b` (Google Gemma 4B parâmetros) para chat e geração de embeddings.
- **Container**: `ollama/ollama:latest` na porta `11434`.
- **GPU**: Configurado com `deploy.resources.reservations.devices` para usar NVIDIA GPU via `nvidia` driver.
- **Modelo de chat**: `gemma4:e4b` — Gemma 4B com 4-bit quantization.
- **Modelo de embeddings**: `gemma4:e4b` (via `/api/embeddings`) ou `nomic-embed-text` (alternativa).
- **Configuração**: `num_predict=2048`, `temperature=0.7`, `keep_alive="10m"`.

### LangChain 1.x
- **Propósito**: Framework para construir aplicações com LLMs (orquestração, agentes, chains, memória, RAG).
- **Uso principal**:
  - **Agents**: `create_tool_calling_agent` + `AgentExecutor` — permite ao LLM decidir qual tool chamar (16 tools do Spotify).
  - **RAG**: `RecursiveCharacterTextSplitter` para chunking, `create_stuff_documents_chain` para síntese.
  - **Memory**: `DbChatMessageHistory` — histórico de conversas persistido no PostgreSQL.
- **Pacotes**:
  - `langchain` — framework principal
  - `langchain-core` — abstrações base (messages, tools, LCEL)
  - `langchain-ollama` — integração com Ollama (`ChatOllama`)
  - `langchain-openai` — integração com APIs OpenAI-compatible (`ChatOpenAI` para IFES Colatina)
  - `langchain-community` — integrações da comunidade (`DbChatMessageHistory`)
  - `langchain-text-splitters` — splitters de texto (`RecursiveCharacterTextSplitter`)

### LangChain Agents (Tool Calling)
- **Propósito**: Permitir que o LLM execute ações no mundo real (Spotify) via function calling.
- **Uso**: 16 tools definidas em `backend/app/agents/tools.py`:
  - **Busca**: `buscar_musica`, `buscar_artista`, `buscar_album`, `pesquisar_spotify`
  - **Dados do usuário**: `minha_musica_recente`, `meus_top_musicas`, `meus_top_artistas`, `minhas_musicas_curtidas`
  - **Playlists**: `minhas_playlists`, `criar_playlist`, `adicionar_musica_playlist`, `criar_playlist_inteligente`
  - **Playback**: `tocar_musica`, `tocar_playlist`, `pausar_musica`, `proxima_musica`, `musica_anterior`
  - **Fila**: `adicionar_musica_fila`, `adicionar_lista_fila`
  - **Dispositivos**: `mudar_dispositivo`, `listar_dispositivos`
- **Streaming**: `AgentExecutor.stream()` com chunks em tempo real via SSE.
- **Configuração**: `max_iterations=5`, `handle_parsing_errors=True`, `return_direct=True` nas tools de execução.

### RAG (Retrieval-Augmented Generation)
- **Propósito**: Base de conhecimento musical — o LLM busca documentos relevantes antes de responder.
- **Fluxo**:
  1. Documento enviado (PDF, URL, texto) → extração de texto
  2. Chunking via `RecursiveCharacterTextSplitter` (chunk=600, overlap=100)
  3. Geração de embeddings (Ollama `/api/embeddings` ou Sentence Transformers)
  4. Armazenamento no PostgreSQL com pgvector
  5. Na consulta: busca top-5 fragmentos por distância cosseno → síntese via LLM
- **Verificação de duplicata**: Threshold de similaridade vetorial 0.15.
- **Fluxo de aprovação**: Documentos passam por pendente → aprovado/rejeitado por moderador.

### Sentence Transformers
- **Propósito**: Geração de embeddings de alta qualidade para RAG.
- **Uso**: Biblioteca para carregar e executar modelos de embeddings localmente.
- **Modelo alvo**: `google/embeddinggemma-300m` — embedding especializado para similaridade semântica.
- **Status atual**: Embeddings via Ollama (mais leve). Sentence Transformers com GPU é o plano futuro para melhor qualidade.
- **Pacote**: `pip install git+https://github.com/huggingface/transformers@v4.56.0-Embedding-Gemma-preview`

---

## 4. APIs Externas

### Spotify Web API
- **Propósito**: Fonte primária de dados musicais e controle de playback.
- **Uso**: Perfil do usuário, playlists, top tracks/artists, busca, playback remoto, dispositivos.
- **Autenticação**: OAuth2 com PKCE (Authorization Code + PKCE).
- **Pacote Python**: `spotipy>=2.24`
- **Endpoints principais**:
  - `/v1/me` — perfil do usuário
  - `/v1/me/player` — controle de playback
  - `/v1/me/top/{type}` — top tracks/artists
  - `/v1/me/tracks` — músicas curtidas/salvas
  - `/v1/search` — busca global
  - `/v1/playlists/{id}` — playlists
  - `/v1/recommendations` — recomendações (planejado)

### ReccoBeats API
- **Propósito**: API externa de recomendação musical e audio features.
- **Uso**: Complementa dados de áudio (danceability, energy, valence, tempo, key, etc.) e recomendação.
- **Módulo**: `backend/app/reccobeats/`

### Wikipedia API
- **Propósito**: Extração de artigos para enriquecer a base de conhecimento RAG.
- **Uso**: Script `dowloadWikipedia.py` baixa artigos sobre temas musicais.
- **Pacote**: `wikipedia>=1.4.0`

---

## 5. Frontend

### React 18
- **Propósito**: Biblioteca JavaScript para construção da interface de usuário (SPA).
- **Uso**: Toda a interface — chat, dashboard, perfil, autenticação, base de conhecimento.
- **Pacote**: `react@^18.3.1` + `react-dom@^18.3.1`

### TypeScript 5.8 (strict mode)
- **Propósito**: Superset tipado de JavaScript.
- **Uso**: Todo o frontend é escrito em TypeScript com modo estrito habilitado.
- **Configuração** (`tsconfig.app.json`): `strict: true`, `noImplicitAny: true`, `noUnusedLocals: true`, `noUnusedParameters: true`, `strictNullChecks: true`, `noFallthroughCasesInSwitch: true`.
- **Pacote**: `typescript@^5.8.3`

### Vite 7
- **Propósito**: Build tool e dev server ultrarrápido.
- **Uso**: Compilação, HMR (Hot Module Replacement), bundling para produção.
- **Pacote**: `vite@^7.0.0`

### Tailwind CSS 3.4
- **Propósito**: Framework CSS utility-first para estilização.
- **Uso**: Todas as páginas e componentes usam classes utilitárias Tailwind.
- **Configuração**: `tailwind.config.ts` — fonte Figtree, tema extendido com cores do projeto.
- **Pacote**: `tailwindcss@^3.4.17`

### shadcn/ui (Radix UI)
- **Propósito**: Biblioteca de componentes React acessíveis e customizáveis.
- **Uso**: Componentes de UI: Accordion, Alert Dialog, Avatar, Button, Card, Checkbox, Dialog, DropdownMenu, Form, Input, Label, Popover, Progress, Select, Separator, Slider, Switch, Tabs, Toast, Toggle, Tooltip, e mais.
- **Pacotes**: `@radix-ui/react-*` (27 pacotes, apenas ~2 efetivamente usados).

### React Router DOM 6
- **Propósito**: Roteamento client-side para SPA.
- **Uso**: Define rotas para Chat, Dashboard, Profile, Login, Cadastro, AuthCallback, RecuperarSenha, ResetSenha, BaseConhecimento, NotFound.
- **Pacote**: `react-router-dom@^6.30.1`

### react-markdown + remark-gfm
- **Propósito**: Renderização de Markdown nas mensagens do chat.
- **Uso**: Converte texto com formatação Markdown (negrito, itálico, código, listas, links, tabelas) em HTML renderizado.
- **Pacotes**: `react-markdown@^10.1.0`, `remark-gfm@^4.0.1` (suporte a GitHub Flavored Markdown).

### React Hook Form + Zod
- **Propósito**: Gerenciamento de formulários com validação.
- **Uso**: Formulários de login, cadastro, recuperação de senha com validação schema-based.
- **Pacotes**: `react-hook-form@^7.61.1`, `zod@^3.25.76`, `@hookform/resolvers@^3.10.0`

### Recharts
- **Propósito**: Biblioteca de gráficos para React.
- **Uso**: Dashboard com gráficos de métricas e analytics.
- **Pacote**: `recharts@^2.15.4`

### Framer Motion
- **Propósito**: Animações declarativas para React.
- **Uso**: Animações de transição e micro-interações na interface.
- **Pacote**: `framer-motion@^12.35.1`

### Outras bibliotecas Frontend
- **@tanstack/react-query** — Gerenciamento de estado assíncrono e cache de requisições.
- **date-fns** — Manipulação e formatação de datas.
- **lucide-react** — Ícones SVG.
- **class-variance-authority + clsx + tailwind-merge** — Utilitários para classes condicionais e merge Tailwind.
- **cmdk** — Menu de comandos (paleta de atalhos).
- **react-day-picker** — Date picker.
- **embla-carousel-react** — Carrossel.
- **sonner** — Toast notifications (substituído por shadcn/ui toast).

### DevDependencies
- **@vitejs/plugin-react-swc** — Plugin Vite para React com SWC (compilador rápido).
- **ESLint** — Linting (`eslint@^9.32.0`).
- **Vitest** — Test runner compatível com Vite (`vitest@^3.2.4`).
- **PostCSS + Autoprefixer** — Processamento CSS.
- **Tailwind CSS Typography** — Plugin para estilos de tipografia (`@tailwindcss/typography`).
- **Testing Library** — Testes de componentes React (`@testing-library/react`, `@testing-library/jest-dom`).
- **jsdom** — Ambiente DOM para testes.

---

## 6. Autenticação & Segurança

### JWT (JSON Web Tokens)
- **Propósito**: Autenticação stateless.
- **Uso**: Token gerado no login (Spotify ou email/senha), armazenado no `localStorage` do frontend, enviado em todas as requisições via header `Authorization: Bearer <jwt>`.
- **Pacote**: `flask-jwt-extended`

### OAuth2 Spotify (PKCE)
- **Propósito**: Autenticação via conta Spotify.
- **Uso**: Fluxo Authorization Code with PKCE — o usuário autoriza no Spotify, recebe code, backend troca por access token + refresh token.
- **Scopes**: `user-read-private`, `user-read-email`, `user-top-read`, `user-library-read`, `playlist-modify-public`, `playlist-modify-private`, `user-modify-playback-state`, `user-read-playback-state`, `user-read-currently-playing`.
- **Pacote**: `spotipy>=2.24`

### SMTP / Gmail
- **Propósito**: Envio de emails transacionais (recuperação de senha).
- **Uso**: Endpoint `POST /auth/forgot-password` envia email com link contendo JWT de 1h. Endpoint `POST /auth/reset-password` valida token e atualiza senha.
- **Configuração**: Env vars `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER`, `SMTP_PASS` (App Password do Google), `SMTP_FROM`.

### bcrypt
- **Propósito**: Hashing de senhas.
- **Uso**: Senhas dos usuários (login custom) são hasheadas com bcrypt antes de armazenar no banco.

---

## 7. Containerização & Infraestrutura

### Docker / Docker Compose
- **Propósito**: Containerização e orquestração de todos os serviços.
- **Uso**: 6 serviços definidos em `docker-compose.yml`:
  1. **db** — PostgreSQL + pgvector (porta 5432)
  2. **ollama** — Servidor LLM local com GPU (porta 11434)
  3. **ollama-init** — Container init que baixa o modelo `gemma4:e4b`
  4. **backend** — API Flask + Gunicorn (porta 5000)
  5. **frontend** — Nginx servindo build React (porta 8080)
  6. **pgadmin** — Interface gráfica PostgreSQL (porta 5050)
- **Profile**: `tunnel` — Cloudflare Tunnel para link público (só sobe com `--profile tunnel`).

### Nginx 1.27
- **Propósito**: Proxy reverso e servidor de arquivos estáticos.
- **Uso**: Servir o SPA React buildado e fazer proxy reverso para o backend Flask.
- **Configurações específicas**:
  - `proxy_pass http://backend:5000/` — redireciona `/api/*` para o backend
  - `proxy_buffering off` — desabilita buffer para streaming SSE
  - `chunked_transfer_encoding on` — habilita transferência chunked
  - `add_header X-Accel-Buffering no` — desabilita buffer do Cloudflare
  - `proxy_pass_header Set-Cookie` — preserva cookies de sessão (OAuth PKCE)
  - Timeouts longos: `proxy_connect_timeout 360s`, `proxy_send_timeout 360s`, `proxy_read_timeout 360s`

### Cloudflare Tunnel (cloudflared)
- **Propósito**: Criar link público temporário (trycloudflare.com) para o ambiente local.
- **Uso**: Container Docker com profile `tunnel`. Conecta ao frontend via Docker DNS (`frontend:80`).
- **Container**: Alpine Linux com binário oficial `cloudflared`.
- **Limitação**: A cada novo link, é necessário adicionar a redirect URI no Dashboard do Spotify Developer.

---

## 8. Protocolos & Padrões

### SSE (Server-Sent Events)
- **Propósito**: Streaming unidirecional de dados do servidor para o cliente.
- **Uso**: Respostas do chat são enviadas em chunks via SSE — o frontend exibe o texto conforme é gerado pelo LLM.
- **Implementação**: Flask `Response` com `mimetype='text/event-stream'`, generator com `yield` de chunks.

### MCP (Model Context Protocol)
- **Propósito**: Protocolo aberto para expor ferramentas de IA como serviços padronizados.
- **Uso**: Servidor MCP standalone (`backend/app/mcp_server.py`) expõe 13 tools do Spotify para consumo por clientes MCP (Claude Desktop, Insomnia).
- **Pacote**: `mcp>=1.0.0`

### Repository Pattern
- **Propósito**: Abstração de acesso a dados.
- **Uso**: Cada módulo do backend tem um Repository que encapsula queries SQLAlchemy. O Service layer usa o Repository, nunca acessa o banco diretamente.

### Blueprint Pattern
- **Propósito**: Organização modular de rotas Flask.
- **Uso**: Cada módulo é um Flask Blueprint com seu próprio `url_prefix` (ex: `/auth`, `/chat`, `/spotify`, `/rag`, `/dashboard`, `/api/llm-provider`).

### Service Layer
- **Propósito**: Separação de lógica de negócio das rotas HTTP.
- **Uso**: Blueprints delegam para Services, que contêm a lógica de negócio e orquestram Repositories.

---

## 9. Documentação & Testes

### Documentação do Projeto (cline_docs/)
- `project_overview.md` — Visão geral e funcionalidades
- `architecture.md` — Arquitetura detalhada e fluxo de dados
- `decisions.md` — Decisões técnicas e justificativas
- `tecnologias.md` — Este documento
- `bugs_fixed.md` — Histórico de bugs corrigidos
- `next_steps.md` — Status do projeto e próximos passos
- `code_review_fase_atual.md` — Revisão de código atual
- `analise_hardcoded_refatoracao.md` — Análise de hardcoded e sugestões de refatoração
- `arquitetura_rag_langchain.md` — Detalhamento do RAG + LangChain
- `ifes_colatina_integracao.md` — Guia de integração com IFES Colatina
- `security_checklist.md` — Checklist de segurança
- `decisao_user_preferences.md` — Regras de execução para o Cline
- `Casos de Uso Detalhados — Chatbot de Música.pdf` — Documento de requisitos
- `RequisitosSistemaChatbot.pdf` — Documento de requisitos original

### Testes
- **Vitest**: Test runner para o frontend (`vitest@^3.2.4`)
- **Testing Library**: Testes de componentes React
- **Insomnia**: Coleção de testes de API (`insomnia_musicbot_tests.json`)

---

## 10. Utilitários

### pypdf
- **Propósito**: Extração de texto de arquivos PDF.
- **Uso**: Upload de documentos PDF para a base RAG.
- **Pacote**: `pypdf>=4.0`

### reportlab
- **Propósito**: Geração de arquivos PDF.
- **Uso**: Export de conversas do chat em formato PDF.
- **Pacote**: `reportlab>=4.0`

### faker
- **Propósito**: Geração de dados falsos para desenvolvimento/testes.
- **Uso**: `populate_mock_data.py` — popular banco com dados de exemplo.
- **Pacote**: `faker`

### dotenv
- **Propósito**: Carregar variáveis de ambiente de arquivo `.env`.
- **Pacote**: `dotenv`

### check_embedding.py
- **Propósito**: Script standalone para verificar a qualidade dos embeddings gerados.
- **Uso**: Teste manual da similaridade vetorial entre textos.

### insomnia_musicbot_tests.json
- **Propósito**: Coleção de testes de API para o Insomnia REST Client.
- **Uso**: Testar endpoints manualmente durante desenvolvimento.

---

## Resumo Visual

```
                    ┌─────────────────────────────────┐
                    │         Frontend (Browser)        │
                    │  React 18 + TypeScript 5.8        │
                    │  Vite 7 + Tailwind 3.4            │
                    │  shadcn/ui + Radix UI             │
                    └──────────────┬──────────────────┘
                                   │ HTTP + SSE (JWT)
                    ┌──────────────▼──────────────────┐
                    │     Nginx 1.27 (proxy reverso)   │
                    │  Porta 8080, buffering off       │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │     Backend (Flask + Gunicorn)    │
                    │  Python 3.12, Porta 5000          │
                    │  ┌──────────────────────────┐     │
                    │  │ LangChain 1.x            │     │
                    │  │  ├ Agents (16 tools)     │     │
                    │  │  ├ RAG (embeddings+pgvec)│     │
                    │  │  └ Memory (DbHistory)    │     │
                    │  └──────────────────────────┘     │
                    └──────┬──────────────┬─────────────┘
                           │              │
              ┌────────────▼──┐  ┌────────▼──────────┐
              │ PostgreSQL 16 │  │  Ollama (GPU)      │
              │ + pgvector    │  │  gemma4:e4b        │
              │ (Porta 5432)  │  │  (Porta 11434)     │
              └───────────────┘  └───────────────────┘

     Serviços Externos:
     ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌─────────┐
     │ Spotify  │  │ReccoBeats│  │ IFES      │  │ SMTP    │
     │ Web API  │  │ API      │  │ Colatina  │  │ Gmail   │
     └──────────┘  └──────────┘  └───────────┘  └─────────┘

     Auxiliares:
     ┌────────────┐  ┌──────────────────┐
     │ pgAdmin4   │  │ Cloudflare Tunnel│
     │ (Porta 5050)│  │ (trycloudflare)  │
     └────────────┘  └──────────────────┘
```

---

> **Última atualização**: 19/06/2026