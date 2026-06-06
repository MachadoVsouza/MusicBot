"""
Agents do LangChain para interagir com as tools do Spotify.
Usa apenas langchain-core (sem dependência de langchain-community/agents).
"""
import logging
import json
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.langchain.client import get_llm
from .tools import make_spotify_tools

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """Você é o MusicBot, um assistente musical inteligente e apaixonado por música.

Você tem acesso a ferramentas do Spotify para ajudar o usuário com sua biblioteca musical.

## Quando usar ferramentas:
- buscar_musica: usuário quer ouvir/encontrar uma música específica
- musicas_recentes: usuário pergunta o que ouviu recentemente
- top_musicas / top_artistas: usuário pergunta seus favoritos/mais ouvidos
- musicas_curtidas: usuário pergunta sobre músicas salvas/curtidas
- listar_playlists: usuário pergunta sobre suas playlists
- criar_playlist: usuário quer criar uma nova playlist
- adicionar_musica_playlist: usuário quer adicionar música a playlist existente
- buscar_artista: usuário quer informações sobre um artista
- tocar_musica: usuário PEDIU PARA TOCAR uma música AGORA (ex: "toca Creep")
- mudar_dispositivo: usuário quer MUDAR DE DISPOSITIVO (ex: "toca no celular", "muda pra caixa de som")
- tocar_playlist: usuário PEDIU PARA TOCAR uma playlist
- pausar_musica: usuário PEDIU PARA PAUSAR a música
- proxima_faixa / faixa_anterior: usuário quer pular/voltar música
- adicionar_fila / adicionar_lista_fila: usuário quer adicionar na fila
- criar_playlist_inteligente: usuário mandou uma LISTA de músicas

## Quando NÃO usar ferramentas:
- Perguntas gerais sobre música, história, teoria musical
- Curiosidades sobre artistas que não precisam de dados em tempo real
- Conversas casuais

## Diretrizes de resposta:
- Responda SEMPRE em português brasileiro
- Seja detalhado e completo — desenvolva bem a resposta
- Quando encontrar uma música com preview disponível, mencione que o usuário pode ouvir 30 segundos
- Se uma ferramenta retornar erro, explique claramente e sugira alternativas
- Nunca corte a resposta no meio — sempre conclua o raciocínio
- Demonstre entusiasmo e conhecimento musical

## IMPORTANTE: Ferramentas de execução automática
As seguintes ferramentas JÁ retornam uma mensagem pronta para o usuário.
Quando chamá-las, NÃO adicione texto extra — apenas repita o resultado que elas devolveram:
- tocar_musica: já retorna "Música tocando no seu Spotify!" ou o erro
- tocar_playlist: já retorna "Tocando no seu Spotify!" ou o erro
- pausar_musica, proxima_faixa, faixa_anterior: já têm mensagem pronta
- adicionar_fila, adicionar_lista_fila: já retornam "Música adicionada à fila!"
- criar_playlist_inteligente: já retorna o resumo completo"""


def _run_tools(tools: list, tool_calls: list[dict]) -> list:
    """Executa uma lista de tool_calls e retorna os resultados."""
    results = []
    tool_map = {t.name: t for t in tools}
    for tc in tool_calls:
        tool_name = tc.get("name", "")
        tool_args = tc.get("args", {})
        if tool_name in tool_map:
            try:
                result = tool_map[tool_name].invoke(tool_args)
                results.append({"tool": tool_name, "result": result})
            except Exception as e:
                results.append({"tool": tool_name, "result": f"Erro: {e}"})
    return results


def run_agent(token: str, mensagem: str, historico: list[dict]) -> dict:
    """
    Executa o agente de forma não-streaming.
    Usa o LLM com tool calling via bind_tools.
    """
    try:
        llm   = get_llm()
        tools = make_spotify_tools(token)

        # Converte histórico para mensagens LangChain
        messages = [("system", AGENT_SYSTEM_PROMPT)]
        for msg in historico:
            if msg["role"] == "user":
                messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(("ai", msg["content"]))
        messages.append(("human", mensagem))

        prompt = ChatPromptTemplate.from_messages(messages)

        # Bind das tools no LLM
        llm_with_tools = llm.bind_tools(tools)

        chain = prompt | llm_with_tools
        result = chain.invoke({})

        resposta = result.content if hasattr(result, "content") else str(result)
        midia = None

        # Se houver tool_calls na resposta, executa as ferramentas
        if hasattr(result, "tool_calls") and result.tool_calls:
            tool_results = _run_tools(tools, result.tool_calls)
            for tr in tool_results:
                r = tr["result"]
                if isinstance(r, dict) and r.get("preview_url"):
                    midia = {
                        "tipo":        "audio",
                        "preview_url": r["preview_url"],
                        "nome":        r.get("nome"),
                        "artista":     r.get("artista"),
                        "url":         r.get("url"),
                    }

        return {"resposta": resposta, "midia": midia, "usou_agent": True}

    except Exception:
        logger.exception("Erro no agent")
        return {
            "resposta":   "Desculpe, tive um problema ao processar sua mensagem. Tente novamente.",
            "midia":      None,
            "usou_agent": True,
        }


def run_agent_stream(token: str, mensagem: str, historico: list[dict]):
    """
    Generator que produz chunks do agent em tempo real.
    """
    try:
        import time
        llm   = get_llm()
        tools = make_spotify_tools(token)

        messages = [("system", AGENT_SYSTEM_PROMPT)]
        for msg in historico:
            if msg["role"] == "user":
                messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(("ai", msg["content"]))
        messages.append(("human", mensagem))

        prompt = ChatPromptTemplate.from_messages(messages)
        llm_with_tools = llm.bind_tools(tools)
        chain = prompt | llm_with_tools

        midia = None

        # Tenta stream se o LLM suportar
        try:
            for chunk in chain.stream({}):
                if hasattr(chunk, "content") and chunk.content:
                    yield {"type": "token", "content": chunk.content}
                if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                    for tcc in chunk.tool_call_chunks:
                        yield {"type": "tool_call", "tool": tcc.get("name", ""), "tool_input": str(tcc.get("args", ""))}
        except TypeError:
            # Fallback: invoke normal e quebra em chunks
            result = chain.invoke({})
            resposta = result.content if hasattr(result, "content") else str(result)
            CHUNK_SIZE = 20
            for i in range(0, len(resposta), CHUNK_SIZE):
                yield {"type": "token", "content": resposta[i:i + CHUNK_SIZE]}
            if hasattr(result, "tool_calls") and result.tool_calls:
                tool_results = _run_tools(tools, result.tool_calls)
                for tr in tool_results:
                    r = tr["result"]
                    if isinstance(r, dict) and r.get("preview_url"):
                        midia = {
                            "tipo":        "audio",
                            "preview_url": r["preview_url"],
                            "nome":        r.get("nome"),
                            "artista":     r.get("artista"),
                            "url":         r.get("url"),
                        }

        if midia:
            yield {"type": "midia", "midia": midia}
        yield {"type": "done"}

    except Exception:
        logger.exception("Erro no agent stream")
        yield {
            "type":    "error",
            "content": "Desculpe, tive um problema ao processar sua mensagem. Tente novamente.",
        }
        yield {"type": "done"}