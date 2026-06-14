"""
Agents do LangChain para interagir com as tools do Spotify.
Usa apenas langchain-core (sem dependencia de langchain-community/agents).
"""
import logging
import json
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.langchain.client import get_llm
from .tools import make_spotify_tools

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """Voce eh o MusicBot, um assistente musical inteligente e entusiasta.

## Ferramentas Disponiveis
Você tem acesso a ferramentas do Spotify para ajudar o usuário com sua biblioteca musical.

## Quando usar cada ferramenta:
- **tocar_musica**: usuario pede para tocar musica AGORA ("toca X", "play X", "bota X pra tocar")
- **tocar_playlist**: usuario pede para tocar uma playlist especifica
- **pausar_musica**: "pausa", "para a musica", "para tudo"
- **proxima_faixa / faixa_anterior**: pular/voltar musica
- **adicionar_fila / adicionar_lista_fila**: "adiciona X na fila"
- **mudar_dispositivo**: "toca no celular", "muda pra caixa de som"
- **buscar_musica**: procurar musica especifica ("procura X", "busca Y")
- **buscar_artista**: informacoes sobre um artista
- **musicas_recentes**: "o que ouvi recentemente", "ultimas tocadas"
- **top_musicas / top_artistas**: "meus favoritos", "mais ouvidos"
- **musicas_curtidas**: "minhas curtidas", "musicas salvas"
- **listar_playlists**: "minhas playlists"
- **criar_playlist**: usuario quer criar playlist nova
- **criar_playlist_inteligente**: usuario manda LISTA de musicas para criar playlist

## Diretrizes de Resposta
- Responda SEMPRE em portugues brasileiro
- Apos executar uma acao, confirme de forma natural (ex: "Tocando Creep no seu Spotify!")
- Se der erro, explique claramente e sugira alternativa
- Para ferramentas que ja retornam mensagem pronta (tocar_musica, tocar_playlist, pausar, fila): NAO adicione texto extra, apenas repita o resultado
- Para ferramentas de busca/listagem: resuma os resultados de forma organizada
- Se houver preview de musica disponivel, mencione: "Voce pode ouvir 30 segundos do preview"
- Seja entusiasta mas direto — o usuario quer acao rapida, nao discurso

## Anti-Alucinacao
- Nunca invente musicas, artistas ou playlists que nao existem
- Se nao encontrar o que o usuario pediu, seja honesto: "Nao encontrei X no Spotify, tente com outro nome"
"""


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
    Executa o agente de forma nao-streaming.
    Usa o LLM com tool calling via bind_tools.
    """
    try:
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
        result = chain.invoke({})

        resposta = result.content if hasattr(result, "content") else str(result)
        midia = None

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

        try:
            for chunk in chain.stream({}):
                if hasattr(chunk, "content") and chunk.content:
                    yield {"type": "token", "content": chunk.content}
                if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                    for tcc in chunk.tool_call_chunks:
                        yield {"type": "tool_call", "tool": tcc.get("name", ""), "tool_input": str(tcc.get("args", ""))}
        except TypeError:
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