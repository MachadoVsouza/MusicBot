# Integração com Workstations Colatina (IFES)

## Visão Geral

O IFES Colatina disponibiliza um proxy com autenticação que expõe modelos Ollama (como `gemma3:12b`, `qwen3.5:0.8b`) por meio de:

- **Rotas nativas do Ollama** (`/api/generate`, `/api/chat`, `/api/embed`, `/api/embeddings`)
- **APIs compatíveis com OpenAI** (`/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, `/v1/models`)
- **Endpoint experimental** (`/v1/messages`)

**URL base:** `https://workstations.chatbotintegracar.online`

---

## Autenticação

Todos os endpoints (exceto `/api/version`, `/api/tags`, `/api/show`, `/api/ps`) exigem:

```
Authorization: Bearer <SUA_API_KEY>
```

**Onde obter a chave:** No painel web do projeto, acesse **API Keys**, crie uma chave e mantenha em segredo.

**Rotas SEM autenticação** (públicas):
- `GET /api/tags`
- `GET /api/show`
- `GET /api/ps`
- `GET /api/version`

**Rotas BLOQUEADAS** (não expostas pelo proxy):
- `/api/pull`, `/api/push`, `/api/create`, `/api/copy`, `/api/delete`, `/api/blobs/*`

---

## Endpoints Disponíveis

### Endpoints Protegidos (exigem API Key)

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/generate` | Geração simples (Ollama nativo) |
| POST | `/api/chat` | Chat com histórico (Ollama nativo) |
| POST | `/api/embed` | Embedding único (Ollama nativo) |
| POST | `/api/embeddings` | Embeddings em lote (Ollama nativo) |
| POST | `/v1/chat/completions` | Chat OpenAI-compatible |
| POST | `/v1/completions` | Completion OpenAI-compatible |
| POST | `/v1/embeddings` | Embeddings OpenAI-compatible |
| GET | `/v1/models` | Listar modelos disponíveis |
| POST | `/v1/messages` | Endpoint experimental |

### Endpoints Públicos (sem autenticação)

- `GET /api/tags` — Lista modelos disponíveis no servidor
- `GET /api/show` — Mostra detalhes de um modelo
- `GET /api/ps` — Processos em execução
- `GET /api/version` — Versão do Ollama

---

## Códigos de Resposta HTTP

| Código | Significado |
|---|---|
| 200/201 | Requisição processada com sucesso |
| 403 | API Key inválida ou endpoint bloqueado |
| 404 | Rota não permitida no proxy |
| 5xx | Erro do upstream (Ollama) ou infraestrutura |

---

## Modelos Disponíveis

- `gemma3:12b` — Google Gemma 3 (12B parâmetros)
- `qwen3.5:0.8b` — Qwen 3.5 (0.8B parâmetros, mais leve)
- (consultar `GET /api/tags` para lista completa)

---

## Exemplos de Consumo

### Python (OpenAI-like com `requests`)

```python
import os
import requests

url = f"{os.environ['OLLAMA_BASE_URL']}/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}",
    "Content-Type": "application/json",
}
payload = {
    "model": "gemma3:12b",
    "messages": [{"role": "user", "content": "Resuma o CAR em 3 tópicos."}],
}

resp = requests.post(url, headers=headers, json=payload, timeout=120)
resp.raise_for_status()
print(resp.json()["choices"][0]["message"]["content"])
```

### Python (Ollama nativo com `httpx`)

```python
import os
import httpx

with httpx.Client(timeout=120) as client:
    response = client.post(
        f"{os.environ['OLLAMA_BASE_URL']}/api/generate",
        headers={"Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}"},
        json={"model": "qwen3.5:0.8b", "prompt": "Explique o CAR."},
    )
    response.raise_for_status()
    print(response.json())
```

### Python (SDK OpenAI oficial)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OLLAMA_API_KEY"],
    base_url=f"{os.environ['OLLAMA_BASE_URL']}/v1",
)

resp = client.chat.completions.create(
    model="gemma3:12b",
    messages=[{"role": "user", "content": "O que é CAR?"}],
)
print(resp.choices[0].message.content)
```

### Python (com Agno)

```python
import os
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.models.ollama import Ollama

agent = Agent(
    model=OpenAILike(
        id='gemma3:12b',
        name='Ollama Workstation Colatina',
        api_key=os.getenv('OLLAMA_API_KEY'),
        base_url='https://workstations.chatbotintegracar.online/v1',
    ),
    markdown=True,
)
agent.print_response('O que é cadastro ambiental rural?', stream=True)
```

### JavaScript (fetch)

```javascript
const response = await fetch(
  `${process.env.OLLAMA_BASE_URL}/v1/chat/completions`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.OLLAMA_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gemma3:12b",
      messages: [{ role: "user", content: "Explique o CAR." }],
    }),
  }
);
if (!response.ok) throw new Error(await response.text());
const data = await response.json();
console.log(data.choices[0].message.content);
```

### JavaScript (fetch com Ollama nativo)

```javascript
const response = await fetch(
  `${process.env.OLLAMA_BASE_URL}/api/chat`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.OLLAMA_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "qwen3.5:0.8b",
      messages: [{ role: "user", content: "Explique o CAR em 2 frases." }],
    }),
  }
);
const data = await response.json();
console.log(data);
```

### Node.js (SDK OpenAI)

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.OLLAMA_API_KEY,
  baseURL: `${process.env.OLLAMA_BASE_URL}/v1`,
});

const completion = await client.chat.completions.create({
  model: "gemma3:12b",
  messages: [{ role: "user", content: "O que é CAR?" }],
});
console.log(completion.choices[0].message.content);
```

---

## Configuração Rápida

```bash
# 1. Defina as variáveis de ambiente
export OLLAMA_API_KEY="sua_api_key_aqui"
export OLLAMA_BASE_URL="https://workstations.chatbotintegracar.online"

# 2. Teste o endpoint público (sem auth)
curl "$OLLAMA_BASE_URL/api/version"

# 3. Teste o endpoint protegido
curl "$OLLAMA_BASE_URL/v1/models" \
  -H "Authorization: Bearer $OLLAMA_API_KEY"

# 4. Faça uma requisição de chat
curl "$OLLAMA_BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $OLLAMA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "Explique o que é CAR em 3 linhas."}
    ]
  }'
```

---

## Como Integrar no MusicBot

Para usar as Workstations Colatina como provedor LLM no MusicBot em vez do Ollama local, você precisa:

1. **Configurar as env vars no `docker-compose.yml`** (ou no ambiente):

```yaml
services:
  backend:
    environment:
      - OLLAMA_BASE_URL=https://workstations.chatbotintegracar.online
      - OLLAMA_API_KEY=sua_chave_aqui
      - OLLAMA_MODEL=gemma3:12b
```

2. **No backend, o `langchain/client.py`** já usa `OLLAMA_BASE_URL` e `OLLAMA_MODEL` do `config.py`, então a única mudança é nas env vars.

3. **No `rag/client.py`**, a URL do Ollama para embeddings também usa `OLLAMA_BASE_URL`, que pode ser a mesma ou a local.

4. **Remover o container Ollama local** do `docker-compose.yml` se optar por usar 100% o serviço externo.