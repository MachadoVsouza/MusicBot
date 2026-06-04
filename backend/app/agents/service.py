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


def run_agent(token: str, mensagem: str, historico: list[dict]) -> dict:
    try:
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

        resultado = agent_executor.invoke({
            "input":        mensagem,
            "chat_history": chat_history,
        })

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


def _extrair_midia(resultado: dict) -> dict | None:
    """Extrai preview_url do intermediate_steps do agent."""
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