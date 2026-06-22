# Métricas para Avaliação do MusicBot

Documento de apoio para apresentação à banca. Cobre 7 categorias de métricas baseadas na infraestrutura real implementada no MusicBot.

---

## 1. Feedback de Usuário (Like / Dislike / Report)

### O que mede
A satisfação direta do usuário com as respostas do chatbot, capturada em tempo real via botões de like, dislike e report na interface.

### Como é calculado (Dashboard Service + Repository)
```text
Taxa de Sucesso = likes / (likes + dislikes) × 100
```
- Base de dados: tabela `feedback` com enum `FeedbackTipo` (`like`, `dislike`, `report`)
- Total de likes, dislikes e reports são contabilizados por período (hoje, semana, mês)
- Cada feedback é vinculado a uma resposta específica, usuário e conversa
- Dashboard exibe tabela paginada (20 itens/página) com auto-refresh de 30s
- Exportação disponível em PDF, CSV e JSON

### Como interpretar
| Taxa de Sucesso | Interpretação |
|:---:|---|
| > 80% | Excelente — chatbot entrega respostas satisfatórias na maioria das interações |
| 60–80% | Bom — há espaço para melhorias pontuais |
| < 60% | Ruim — necessidade de revisão do prompt, ferramentas ou base RAG |

### Por que é relevante
- É a métrica mais direta de qualidade percebida pelo usuário
- Feedbacks negativos com comentários permitem identificar falhas específicas
- Reports (bugs) são coletados separadamente para priorização de correções
- Permite análise por período para verificar se melhorias no código aumentaram a satisfação

---

## 2. Qualidade do Código

### O que mede
A estrutura, manutenibilidade e robustez da base de código do MusicBot.

### Dimensões avaliadas

#### 2.1. Arquitetura em Camadas
```
Usuário → Chat Service → Agents (run_agent / run_agent_stream)
                              → LLM (bind_tools) → 19 Tools Spotify
                                     → SpotifyService → SpotifyRepository → API Spotify (Spotipy)
                              → RAG (pgvector + embeddings) → Fragmentos
```
- **19 ferramentas** implementadas com tool calling do LangChain
- **3 camadas** de abstração: Tools → Service → Repository
- Desacoplamento claro entre regras de negócio e acesso a dados

#### 2.2. Tratamento de Erros
- **Repository**: `try/except spotipy.SpotifyException` em todas as chamadas de playback
- **Service**: validação de `None` e retorno de dicionários com chave `"erro"` para falhas
- **Tools**: mensagens de erro em português brasileiro com sugestões alternativas
- **Agent**: captura global de exceções com fallback para mensagem amigável

#### 2.3. Cobertura de Funcionalidades
| Categoria | Ferramentas | Status |
|-----------|:---:|:---:|
| Busca/Consulta | 8 (buscar_musica, musicas_recentes, top_musicas, top_artistas, musicas_curtidas, listar_playlists, buscar_artista, listar_dispositivos) | 100% funcionais |
| Playlist (Write) | 3 (criar_playlist, adicionar_musica_playlist, criar_playlist_inteligente) | 100% funcionais |
| Playback | 8 (tocar_musica, tocar_playlist, pausar_musica, proxima_faixa, faixa_anterior, adicionar_fila, adicionar_lista_fila, mudar_dispositivo) | 100% funcionais |

#### 2.4. Padrões e Boas Práticas
- **LangChain**: Uso de `ChatPromptTemplate`, `bind_tools`, `return_direct` para ferramentas de ação
- **Streaming**: SSE com gerador Python e fallback para `invoke()` caso `stream()` não seja suportado
- **Segurança**: JWT com expiração, tokens Spotify não expostos, CORS configurado
- **Auditoria**: `AuditLog` imutável para ações administrativas (aprovação/rejeição de documentos)

### Por que é relevante
- Código bem estruturado facilita manutenção e evolução contínua
- Tratamento de erros consistente evita que falhas na API Spotify quebrem o chatbot
- Separação em camadas permite testar cada componente isoladamente

---

## 3. Velocidade de Resposta

### O que mede
O tempo que o chatbot leva para responder ao usuário, do envio da mensagem até o primeiro token visível (streaming) ou resposta completa.

### Como é calculado (implícito na arquitetura)
- **Streaming SSE**: Tokens são enviados incrementalmente para o frontend via `chain.stream()`
  - Primeiro token visível quase instantâneo (latência de rede + processamento inicial do LLM)
  - Respota completa chega ao longo de segundos, mantendo o usuário engajado
- **LLM Local (Ollama)**: Modelo Gemma4 rodando com GPU, latência depende do hardware
  - Sem latência de rede externa
  - Velocidade de inferência depende da GPU disponível
- **RAG**: Quando ativado, adiciona consulta vetorial ao PostgreSQL (pgvector) antes da geração
  - Overhead adicional de ~100-500ms para busca de fragmentos relevantes
  - Indicador: campo `usou_rag` na tabela `resposta`

### Como interpretar
| Faixa de Latência | Interpretação |
|---|---|
| < 2s (primeiro token) | Ótimo — streaming começa quase instantaneamente |
| 2–5s (primeiro token) | Aceitável — espera perceptível mas tolerável |
| > 5s (primeiro token) | Ruim — usuário pode achar que travou |
| < 10s (resposta completa) | Ótimo para respostas curtas |
| 10–30s (resposta completa) | Normal para análises detalhadas |

### Por que é relevante
- Chatbots de música exigem resposta rápida ("toca X AGORA")
- Streaming mantém o usuário engajado enquanto a resposta é gerada
- Dual provider (local/IFES) permite comparar latência entre infraestruturas

---

## 4. Precisão e Assertividade

### O que mede
A capacidade do chatbot de entender corretamente a intenção do usuário e executar a ação certa na primeira tentativa.

### Como é calculado

#### 4.1. Taxa de Reformulação
```text
Taxa de Reformulação = chats com >1 pergunta / total de chats × 100
```
- Um chat com mais de 1 pergunta indica que o usuário precisou reformular
- Calculado no `DashboardRepository.get_metricas()` via subquery SQL
- **Ideal**: taxa baixa (usuário resolve na primeira interação)

#### 4.2. Detecção de Intenção Spotify
- Regex `INTENT_PATTERNS` no `chat/service.py` detecta se a mensagem é sobre Spotify
- Se detectado, ativa o Agent com 19 tools; senão, usa LLM puro com RAG
- **Falso positivo**: ativa tools sem necessidade (overhead desnecessário)
- **Falso negativo**: não ativa tools quando o usuário queria ação Spotify

#### 4.3. Tool Calling do LangChain
- O LLM decide qual tool chamar com base no `AGENT_SYSTEM_PROMPT`
- 19 tools disponíveis, cada uma com descrição clara de quando usar
- `return_direct=True` em tools de ação evita que o LLM "enfeite" a resposta

### Como interpretar
| Taxa de Reformulação | Interpretação |
|:---:|---|
| < 10% | Excelente — usuários quase sempre resolvem na primeira mensagem |
| 10–20% | Aceitável — pequena necessidade de esclarecimento |
| > 20% | Preocupante — chatbot não está entendendo bem as intenções |

### Por que é relevante
- Reformular é frustrante para o usuário e gera mais carga no sistema
- Detecção de intenção precisa evita chamadas desnecessárias à API Spotify
- Tool calling correto garante que a ação executada é exatamente a esperada

---

## 5. Cobertura Funcional

### O que mede
Quanto da API do Spotify o chatbot é capaz de controlar.

### Como é calculado
- **19 tools** cobrindo os principais endpoints da API Spotify
- **3 domínios**: Busca/Consulta (8), Playlist/Write (3), Playback/Controle (8)
- Comparação com as funcionalidades nativas do Spotify:

| Funcionalidade Spotify | Coberta pelo MusicBot? | Tool |
|------------------------|:---:|------|
| Buscar música | ✅ | buscar_musica |
| Histórico recente | ✅ | musicas_recentes |
| Top músicas/artistas | ✅ | top_musicas, top_artistas |
| Músicas curtidas | ✅ | musicas_curtidas |
| Listar playlists | ✅ | listar_playlists |
| Criar playlist | ✅ | criar_playlist, criar_playlist_inteligente |
| Adicionar a playlist | ✅ | adicionar_musica_playlist |
| Tocar música | ✅ | tocar_musica |
| Tocar playlist | ✅ | tocar_playlist |
| Pausar | ✅ | pausar_musica |
| Próxima/Anterior | ✅ | proxima_faixa, faixa_anterior |
| Fila de reprodução | ✅ | adicionar_fila, adicionar_lista_fila |
| Mudar dispositivo | ✅ | mudar_dispositivo |
| Informações de artista | ✅ | buscar_artista |
| Listar dispositivos | ✅ | listar_dispositivos |
| Controlar volume | ❌ | — |
| Shuffle/Repeat | ❌ | Disponível no Repository mas sem tool |
| Rádio/Sugestões | ❌ | — |

**Cobertura**: ~79% das funcionalidades mais relevantes do Spotify (15/19)

### Por que é relevante
- Demonstra a completude da integração com a API Spotify
- Funcionalidades não cobertas (volume, shuffle, repeat) já têm suporte no Repository — basta adicionar tools
- Mostra potencial de expansão

---

## 6. Robustez e Confiabilidade

### O que mede
A capacidade do chatbot de continuar funcionando mesmo quando partes do sistema falham.

### Dimensões avaliadas

#### 6.1. Tolerância a Falhas
- **API Spotify offline**: Exceções `SpotifyException` capturadas em todas as chamadas do Repository
- **Dispositivo Spotify indisponível**: Retorna mensagem "Abra o Spotify em algum dispositivo" em vez de erro genérico
- **Música não encontrada**: Retorna `{"erro": "Nenhuma música encontrada..."}` com sugestão de reformulação
- **LLM não suporta streaming**: Fallback automático para `invoke()` com chunking manual (20 chars)

#### 6.2. Rastreabilidade
- `AuditLog`: Todas as ações administrativas registradas (aprovação, rejeição, criação de moderadores)
- `Feedback`: Todos os likes/dislikes/reports com timestamp, usuário e comentário
- `Chat → Pergunta → Resposta → Feedback`: Cadeia completa de rastreamento

#### 6.3. Disponibilidade
- **Docker Compose**: 6 serviços containerizados (db, ollama, backend, frontend, pgadmin, tunnel)
- **Cloudflare Tunnel**: Link público temporário opcional para acesso externo
- **Dual Provider LLM**: Se Ollama local falhar, pode alternar para IFES Colatina

### Por que é relevante
- Um chatbot musical não pode "cair" quando o usuário quer ouvir música
- Falhas na API Spotify não devem quebrar a experiência — apenas reportar o problema
- Rastreabilidade permite auditoria e debugging de problemas reportados

---

## 7. Experiência do Usuário (UX)

### O que mede
A qualidade da interação do usuário com o chatbot, além da precisão técnica.

### Dimensões avaliadas

#### 7.1. Streaming e Percepção de Velocidade
- Respostas em **streaming SSE**: usuário vê o texto sendo digitado em tempo real
- Fallback para chunking manual se o LLM não suportar streaming nativo
- Sensação de rapidez mesmo em respostas longas com RAG

#### 7.2. Feedback Inline
- Botões like/dislike/report em cada resposta do chatbot
- Toggle (ativar/desativar) sem recarregar a página
- DELETE para remover feedback acidental
- Indicadores visuais do estado do feedback

#### 7.3. Formatação e Apresentação
- **Markdown** nas respostas (`react-markdown` + `remark-gfm`)
- Links customizados com badges (domínio visível, abertura em nova aba)
- Exportação de conversas em **TXT, JSON, MD e PDF**
- Dashboard com auto-refresh de 30s

#### 7.4. Transparência
- **Dual provider LLM**: Usuário pode alternar entre Ollama local e IFES Colatina
- **Fonte RAG**: Quando o chatbot usa conhecimento da base, indica a origem
- **Mensagens de erro claras**: Sempre em português, com explicação do que deu errado

#### 7.5. Segurança e Privacidade
- **JWT**: Autenticação com expiração e refresh
- **OAuth2 Spotify (PKCE)**: Token de acesso sem expor senha
- **Login custom**: Email/senha com recuperação via SMTP/Gmail
- Dados do usuário isolados por `spotify_id`

### Por que é relevante
- A melhor IA perde valor se a interface for confusa ou lenta
- Transparência (mostrar fonte, explicar erros) gera confiança no usuário
- Múltiplos formatos de exportação atendem diferentes necessidades

---

## Resumo para Slides

| # | Métrica | Indicador Principal | Como Medir |
|---|---------|---------------------|------------|
| 1 | Feedback | Taxa de sucesso (likes/total) | Dashboard > 80% excelente |
| 2 | Código | 19 tools, 3 camadas, try/except em tudo | Análise de arquitetura |
| 3 | Velocidade | Tempo até primeiro token (streaming) | < 2s ótimo |
| 4 | Precisão | Taxa de reformulação | < 10% excelente |
| 5 | Cobertura | 15/19 funcionalidades Spotify | ~79% das mais relevantes |
| 6 | Robustez | Tolerância a falhas + rastreabilidade | Sempre retorna erro amigável |
| 7 | UX | Stream, feedback inline, export, transparência | Qualitativo |

---

## Conclusão

O MusicBot implementa um sistema completo de métricas para avaliação contínua, cobrindo desde a satisfação direta do usuário (feedback) até métricas técnicas de código, velocidade e robustez. A arquitetura em camadas e o tratamento consistente de erros garantem confiabilidade, enquanto o streaming e o feedback inline proporcionam uma experiência fluida ao usuário final.