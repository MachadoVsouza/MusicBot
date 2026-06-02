import logging
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.langchain.client import get_llm
from .tools import make_spotify_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o MusicBot, um assistente musical inteligente.
Você pode buscar músicas e artistas no Spotify usando as ferramentas disponíveis.
Responda sempre em português, de forma e concisa.

Quando o usuário pedir para buscar, tocar ou ouvir uma música — use a ferramenta buscar_musica.
Quando retornar uma música com preview_url, avise o usuário que ele pode ouvir um trecho de 30 segundos.
Se não encontrar a música, diga claramente que não foi possível encontrar."""


def run_agent(token: str, mensagem: str, historico: list[dict]) -> dict:
    """
    Executa o agent com as tools do Spotify.
    Retorna a resposta e dados de mídia se houver.
    """
    try:
        llm   = get_llm()
        tools = make_spotify_tools(token)

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        agent          = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

        # Converte histórico para formato LangChain
        chat_history = []
        for msg in historico[:-1]:  # exclui a última mensagem (é a atual)
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            else:
                chat_history.append(AIMessage(content=msg["content"]))

        resultado = agent_executor.invoke({
            "input":        mensagem,
            "chat_history": chat_history,
        })

        resposta = resultado.get("output", "Não consegui processar sua mensagem.")

        # Extrai dados de mídia das tool calls se houver
        midia = _extrair_midia(resultado)

        return {
            "resposta":  resposta,
            "midia":     midia,
            "usou_agent": True,
        }

    except Exception as e:
        logger.error("Erro no agent: %s", e)
        return {
            "resposta":   "Desculpe, não consegui processar sua mensagem. Tente novamente.",
            "midia":      None,
            "usou_agent": True,
        }


def _extrair_midia(resultado: dict) -> dict | None:
    """Extrai preview_url e dados da música do resultado do agent."""
    for step in resultado.get("intermediate_steps", []):
        tool_output = step[1] if isinstance(step, tuple) else None
        if isinstance(tool_output, dict) and tool_output.get("preview_url"):
            return {
                "tipo":        "audio",
                "preview_url": tool_output["preview_url"],
                "nome":        tool_output.get("nome"),
                "artista":     tool_output.get("artista"),
                "url":         tool_output.get("url"),
            }
    return None