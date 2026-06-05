import logging
from langchain.agents import create_tool_calling_agent, AgentExecutor
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
- Demonstre entusiasmo e conhecimento musical"""


def _build_agent(token: str, mensagem: str, historico: list[dict]):
    """Constrói e retorna o executor do agent + inputs."""
    llm   = get_llm()
    tools = make_spotify_tools(token)

    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent              = agent,
        tools              = tools,
        verbose            = False,
        max_iterations     = 5,
        handle_parsing_errors = True,
        return_intermediate_steps = True,
    )

    # Converte histórico para mensagens LangChain (exclui a mensagem atual)
    chat_history = []
    for msg in historico[:-1]:
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(AIMessage(content=msg["content"]))

    return agent_executor, {"input": mensagem, "chat_history": chat_history}


def run_agent(token: str, mensagem: str, historico: list[dict]) -> dict:
    """Versão não-streaming — mantida por compatibilidade."""
    try:
        agent_executor, inputs = _build_agent(token, mensagem, historico)
        resultado = agent_executor.invoke(inputs)

        resposta = resultado.get("output") or "Não consegui processar sua mensagem."
        midia    = _extrair_midia(resultado)

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
    Usa agent_executor.stream() para yieldar eventos de tool call + resposta final.

    Yields dicts no formato:
      {"type": "token", "content": "texto parcial"}
      {"type": "tool_call", "tool": "buscar_musica", "tool_input": "..."}
      {"type": "midia", "midia": {...}}
      {"type": "error", "content": "mensagem de erro"}
      {"type": "done"}
    """
    try:
        agent_executor, inputs = _build_agent(token, mensagem, historico)
        midia = None
        intermediate_steps = []

        # stream() itera pelos steps do agent
        for step in agent_executor.stream(inputs):
            if "actions" in step:
                for action in step["actions"]:
                    yield {
                        "type":       "tool_call",
                        "tool":       action.tool,
                        "tool_input": str(action.tool_input),
                    }

            if "steps" in step:
                for s in step["steps"]:
                    intermediate_steps.append(s)

            if "output" in step:
                output_text = step["output"]
                # Quebra em chunks de tamanho fixo para streaming suave
                CHUNK_SIZE = 20
                for i in range(0, len(output_text), CHUNK_SIZE):
                    yield {"type": "token", "content": output_text[i:i + CHUNK_SIZE]}

        # Extrai midia dos intermediate steps
        for action_output in intermediate_steps:
            # action_output é uma tupla (AgentAction, AgentFinish) — pega o segundo elemento
            if isinstance(action_output, tuple):
                output = action_output[1]
            else:
                output = action_output
            if isinstance(output, dict) and output.get("preview_url"):
                midia = {
                    "tipo":        "audio",
                    "preview_url": output["preview_url"],
                    "nome":        output.get("nome"),
                    "artista":     output.get("artista"),
                    "url":         output.get("url"),
                }
                yield {"type": "midia", "midia": midia}
                break

        yield {"type": "done"}

    except Exception:
        logger.exception("Erro no agent stream")
        yield {
            "type":    "error",
            "content": "Desculpe, tive um problema ao processar sua mensagem. Tente novamente.",
        }
        yield {"type": "done"}


def _extrair_midia(resultado: dict) -> dict | None:
    """Extrai preview_url do intermediate_steps do agent (versão não-streaming)."""
    for action, output in resultado.get("intermediate_steps", []):
        if isinstance(output, dict) and output.get("preview_url"):
            return {
                "tipo":        "audio",
                "preview_url": output["preview_url"],
                "nome":        output.get("nome"),
                "artista":     output.get("artista"),
                "url":         output.get("url"),
            }
    return None