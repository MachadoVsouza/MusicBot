# Revisão Geral do Código — MusicBot (06/06/2026)

## Nota Geral: 6.5/10

Pontos fortes: estrutura modular clara, repository pattern, blueprint pattern, streaming SSE, dual provider.
Pontos fracos: orientação a objeto inconsistente, hardcoded values, frontend monolítico.

---

## 1. Backend — Módulos e Orientação a Objeto

### ✅ Nota 8/10 — `auth/`, `spotify/`, `reccobeats/`
Service + Repository bem separados. SpotifyService injeta SpotifyRepository. Fácil de testar.

### ✅ Nota 7/10 — `rag/`
RagService + RagRepository + RagSintese + RagClient.
- Bom: separação de responsabilidades
- Ruim: `rag/repository.py` abre e fecha sessão SQL em cada método (ver item 4 da análise)
- **Sugestão:** Criar `RagRepository` com contexto de sessão (`with_session` decorator)

### ⚠️ Nota 5/10 — `chat/`
- `ChatService` **acoplado**: instancia `ChatRepository`, `OllamaRepository`, `RagService`, `RagSintese` direto no `__init__`
- **Sugestão:** Injeção de dependência nos parâmetros (`chat_repo=None, llm_repo=None, ...`)

### ⚠️ Nota 5/10 — `llm_provider/` (recém-criado)
- Provider atual: 2 arquivos com funções soltas (`local_provider.get_llm()`, `ifes_provider.get_llm()`)
- **Sugestão:** Strategy Pattern com classe abstrata:
  ```python
  class LLMProvider(ABC):
      def get_llm(self, stream=False) -> BaseChatModel: ...
      def get_embeddings(self, texts) -> list: ...
  ```
  + `ProviderFactory.create("ifes", config)` — fácil adicionar OpenAI, Anthropic depois

### ⚠️ Nota 4/10 — `agents/`
- `tools.py`: 314 linhas, **19 tools** declaradas dentro de `make_spotify_tools()`. Tudo aninhado, zero testabilidade individual
- `_resolver_dispositivo()` é uma função interna que depende de `svc` do closure
- **Sugestão 1:** Separar tools em arquivos: `search_tools.py`, `playlist_tools.py`, `playback_tools.py`
- **Sugestão 2:** Criar classe `SpotifyAgent` que recebe `SpotifyService` e expõe os métodos como tools:
  ```python
  class SpotifyAgent:
      def __init__(self, token):
          self.svc = SpotifyService(SpotifyRepository(token))
      def buscar_musica(self, query) -> dict: ...
      def tocar_musica(self, query, device=None) -> str: ...
      def get_tools(self) -> list: ...
  ```

### ❌ Nota 3/10 — `core/auth_guard.py`
- `_is_token_valid()` faz `GET /v1/me` no Spotify **a cada requisição** (rate limit + latência)
- **Sugestão:** Cache com TTL de 5 min, ou tentar a request real e dar refresh só se der 401

---

## 2. Frontend

### ❌ Nota 3/10 → ✅ Nota 6/10 — `Chat.tsx` (530+ linhas)
- Streaming, histórico, feedback, export, provider toggle, mini player, preferências TUDO no mesmo arquivo
- **Melhorias da sessão 07/06**: Adicionado `isModerator` para esconder links Dashboard/Base de usuários comuns
- **Sugestão:** Extrair:
  - `LLMProviderToggle.tsx` (já tem o estado, só mover)
  - `MessageList.tsx` + `MessageBubble.tsx`
  - `MiniPlayer.tsx` (já existe dentro do Chat.tsx)
  - `FeedbackModal.tsx`
  - `ExportMenu.tsx`

### ✅ Nota 8/10 — `BaseConhecimento.tsx`
- Bom: organizado, modal de novo documento, filtros, aprovação/rejeição
- **Corrigido 07/06**: `super_usuario_id: 1` hardcoded → usa `user.superUsuarioId` do contexto
- **Corrigido 07/06**: Tela "Acesso Restrito" para usuários comuns (`!isModerator`)

### ⚠️ Nota 7/10 — `AuthContext.tsx`
- `authFetch` é um helper global útil, mas mistura lógica de auth com chamadas API
- **Melhorias 07/06**: `fetchMeData()` busca role/super_usuario_id do `/api/auth/me`; `isModerator` exposto no contexto
- **Sugestão:** Separar em `api.ts` (fetch wrapper) e `AuthContext.tsx` (só estado de auth)

---

## 3. Banco de Dados

### ✅ Nota 8/10 — `models.py`
- Modelos bem definidos, relacionamentos corretos, uso de enums
- Chave primária composta evitada (spotify_id como PK única é ok para esse domínio)

### ⚠️ Nota 5/10 — Repositories
- Cada método abre e fecha `get_session()`. `aprovar_e_indexar()` faz 3+ sessões separadas
- **Sugestão:** Criar decorator `@with_session` ou método `salvar_completo()` que faz tudo em 1 transação

---

## 4. Configuração

### ⚠️ Nota 6/10 — `config.py`
- `LLM_PROVIDER` como env var é bom, mas `IFES_API_KEY = ""` vazio pode dar 403 silencioso
- `OLLAMA_KEEP_ALIVE = "30s"` muito baixo para produção
- `SPOTIFY_CLIENT_ID` hardcoded no código (segurança?)

---

## 5. Propostas de Refatoração OO (Priorizadas)

| Prioridade | Tarefa | Módulo | Esforço | Impacto |
|---|---|---|---|---|
| 🔴 1 | Provider com Strategy Pattern (classe + factory) | `llm_provider/` | 30min | Alto (extensibilidade) |
| 🔴 2 | Extrair componentes do Chat.tsx | `frontend/` | 1h | Médio (manutenibilidade) |
| 🟡 3 | Remover `super_usuario_id: 1` hardcoded | `BaseConhecimento.tsx` + backend | 15min | Alto (bug) |
| 🟡 4 | Refatorar agents/tools.py em classes | `agents/` | 45min | Médio (testabilidade) |
| 🟡 5 | ChatService com injeção de dependência | `chat/service.py` | 20min | Médio (testes) |
| 🟢 6 | Cache no `_is_token_valid()` | `auth_guard.py` | 15min | Baixo (performance) |
| 🟢 7 | Sessão única nos repositories | `rag/repository.py`, `chat/repository.py` | 20min | Baixo (performance) |
| 🟢 8 | Aumentar `num_predict=4096`, `keep_alive=5m` | `config.py`, `local_provider.py` | 2min | Baixo (qualidade) |

---

## 6. Próxima Fase do Projeto

Após essas correções, a próxima fase sugerida (baseada em `next_steps.md` e no que não foi implementado):

1. **🔴 Sistema de recomendação** — endpoint `/v1/recommendations` do Spotify + integração com ReccoBeats
2. **🔴 Wikipedia automático no RAG** — tool `buscar_wikipedia(tema)` + submissão como documento pendente
3. **🟡 Prune do Ollama / servidor IFES** — trocar modelo local por algo menor (já encaminhado com o dual provider)
4. **🟢 Integração MusicBrainz/Last.fm/Genius** — dados abertos sobre artistas e letras
5. **🟢 Melhorias no Profile.tsx** — playback controls direto na página