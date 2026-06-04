# Próximos Passos (To-Do)

- [x] Memory Bank criado e consolidado
- [x] Migração de session → JWT (flask-jwt-extended)
- [x] Bugs corrigidos (auth nas rotas Spotify, chat streaming, navegação)
- [x] Qualidade LLM ajustada (num_predict, temperature, keep_alive, prompts)
- [x] LangChain Agents com Spotify real e parsing de erros
- [x] RAG com lazy loading, batch embeddings, vector ranking, chunking via LangChain
- [ ] **Cloudflare Tunnel** — link público temporário para compartilhar o projeto
- [ ] **MCP Server** — expor tools do Spotify como MCP para Claude Desktop/Insomnia
- [ ] **RAG com síntese** — RetrievalQA do LangChain em vez de chunks crus no prompt
- [ ] **Memory do LangChain** — substituir histórico manual por RunnableWithMessageHistory
- [ ] **Streaming do agent** — hoje cai no modo normal (fake stream), implementar stream real