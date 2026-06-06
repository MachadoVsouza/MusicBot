# Análise de Código — Hardcoded + Refatoração OO

## 🔴 Hardcoded no Código

### 1. `super_usuario_id: 1` no Frontend (BaseConhecimento.tsx)
**Arquivo:** `frontend/src/pages/BaseConhecimento.tsx` (linha 100 e 109)
```typescript
body: { ..., super_usuario_id: 1 }
fd.append('super_usuario_id', '1');
```
**Problema:** Se não existir SuperUsuario com ID 1 no banco, a requisição falha.
**Solução:**  
- Backend: criar um SuperUsuario default no `populate_mock_data.py`
- Ou: usar o próprio `usuario_id` logado como moderador (buscar moderador do banco)
- Ou: permitir `null` e usar o `uploaded_by` como moderador

### 2. `OLLAMA_MODEL = "qwen:4b"` no config.py
**Arquivo:** `backend/app/config.py` (linha 54)
```python
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen:4b")
```
**Problema:** O modelo no container Docker pode ser diferente. Se `qwen:4b` não existir localmente, o streaming quebra.
**Solução:** Já está com env var, mas documentar que precisa fazer `ollama pull qwen:4b` antes.

### 3. `OLLAMA_KEEP_ALIVE = "30s"` muito baixo
**Arquivo:** `backend/app/config.py` (linha 55)
```python
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30s")
```
**Problema:** 30 segundos faz o Ollama descarregar o modelo rapidamente. Em uso esporádico, cada requisição paga o cold start.
**Solução:** Mudar default para `"5m"` ou `"-1"` (nunca descarrega) em produção.

### 4. `NUM_PREDICT = 2048` fixo no client.py
**Arquivo:** `backend/app/llm_provider/local_provider.py` (linha 15)
```python
num_predict = 2048
```
**Problema:** Respostas longas podem ser cortadas no meio. O prompt do system manda "nunca corte a resposta".
**Solução:** Aumentar para `4096` ou configurar via env var.

### 5. `IFES_API_KEY = ""` default vazia
**Arquivo:** `backend/app/config.py`
```python
IFES_API_KEY = os.getenv("IFES_API_KEY", "")
```
**Problema:** Se a env var não for configurada e o usuário escolher "ifes", a requisição vai falhar com 403.
**Solução:** O service já faz fallback para `local` se o provider não for reconhecido. Mas não valida se a key existe. Adicionar validação no `toggleProvider` do frontend.

### 6. `base_url = "http://ollama:11434"` hardcoded no rag/client.py
**Arquivo:** `backend/app/llm_provider/local_provider.py` (linha 20)
```python
base_url = current_app.config.get("OLLAMA_BASE_URL", "http://ollama:11434")
```
**Problema:** Em dev local a URL é `http://localhost:11434`, em Docker é `http://ollama:11434`. O fallback do `get()` pode pegar o host errado.
**Solução:** Remover fallback hardcoded — confiar na env var configurada no `docker-compose.yml`.

### 7. `llm_provider` com `String(10)` no model
**Arquivo:** `backend/app/database/models.py`
```python
llm_provider: Mapped[str] = mapped_column(String(10), default="local")
```
**Problema:** 10 caracteres é suficiente para "local"/"ifes", mas se no futuro adicionar "openai" (6 chars) cabe. Se adicionar "anthropic" (9 chars) também. Tá ok por ora.

---

## 🟡 Sugestões de Refatoração OO

### 1. Provider com Strategy Pattern (classe abstrata + implementações)

Em vez de 2 arquivos soltos (`local_provider.py`, `ifes_provider.py`), usar uma classe abstrata:

```python
# llm_provider/base.py
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel

class LLMProvider(ABC):
    @abstractmethod
    def get_llm(self, stream: bool = False) -> BaseChatModel:
        pass
    
    @abstractmethod
    def get_embeddings(self, texts: list[str]) -> list[list[float]] | None:
        pass
```

```python
# llm_provider/implementations.py
class LocalProvider(LLMProvider):
    def __init__(self, config):
        self.base_url = config["OLLAMA_BASE_URL"]
        self.model = config["OLLAMA_MODEL"]
    
    def get_llm(self, stream=False):
        return ChatOllama(base_url=self.base_url, model=self.model, ...)
    
    def get_embeddings(self, texts):
        # chamada /api/embeddings no Ollama local
        ...

class IfesProvider(LLMProvider):
    def __init__(self, config):
        self.base_url = config["IFES_BASE_URL"]
        self.api_key = config["IFES_API_KEY"]
        self.model = config["IFES_MODEL"]
    
    def get_llm(self, stream=False):
        return ChatOpenAI(base_url=f"{self.base_url}/v1", ...)
    
    def get_embeddings(self, texts):
        # chamada /api/embeddings no IFES com API Key
        ...
```

```python
# llm_provider/service.py
class ProviderFactory:
    @staticmethod
    def create(provider_name: str, config: dict) -> LLMProvider:
        if provider_name == "ifes":
            return IfesProvider(config)
        return LocalProvider(config)
```

**Vantagens:**
- Fácil adicionar novos providers (OpenAI, Anthropic, etc.) — só criar nova classe
- Código mais testável (mock da interface)
- `service.py` vira um router simples
- Embeddings e LLM sempre juntos (consistência)

### 2. ChatService com Injeção de Dependência
**Atual:** `ChatService` instancia `ChatRepository()`, `OllamaRepository()`, `RagService()`, `RagSintese()` direto no `__init__`.  
**Proposta:** Receber por parâmetro (injeção):
```python
class ChatService:
    def __init__(self, chat_repo=None, llm_repo=None, rag_svc=None, rag_sintese=None):
        self.chat_repo = chat_repo or ChatRepository()
        self.llm_repo = llm_repo or OllamaRepository()
        ...
```
**Vantagem:** Testável com mocks, sem precisar de banco real.

### 3. Separar responsabilidades do Chat.tsx
**Problema:** 530+ linhas com lógica de streaming, histórico, feedback, export, provider toggle, mini player, preferências.  
**Solução:** Extrair em componentes:
- `LLMProviderToggle.tsx` (switch local/ifes)
- `MessageList.tsx` (renderização de mensagens + mini player)
- `ExportMenu.tsx`
- `FeedbackModal.tsx`

### 4. RagRepository com sessão única
**Problema:** Cada método abre e fecha sessão do banco. Operações como `aprovar_e_indexar()` fazem várias chamadas = várias sessões.  
**Solução:** Método `salvar_pergunta_e_resposta()` no `ChatRepository` que faz tudo em 1 transação.

---

## Resumo do que fazer

| Prioridade | O que | Arquivo(s) | Esforço |
|---|---|---|---|
| 🔴 | Criar SuperUsuario default ou remover `super_usuario_id: 1` | `BaseConhecimento.tsx`, `populate_mock_data.py` | 15min |
| 🟡 | Refatorar provider para Strategy Pattern | `llm_provider/` (criar `base.py`, refatorar `service.py`) | 30min |
| 🟡 | Aumentar `num_predict=4096` e `keep_alive=5m` | `local_provider.py`, `config.py` | 2min |
| 🟢 | Extrair componentes do Chat.tsx | `frontend/src/components/` | 1h |
| 🟢 | Injeção de dependência no ChatService | `chat/service.py` | 20min |