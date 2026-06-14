"""
RAG com Sintese — monta o prompt com os fragmentos e chama o LLM diretamente,
em vez de depender de create_stuff_documents_chain (removido no LangChain 1.x).
"""
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from app.langchain.client import get_llm
from .repository import RagRepository

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_SINTESE = """Voce eh o MusicBot, especialista em sintese de informacoes musicais.

## Tarefa
Responda a pergunta do usuario baseando-se PRIMARIAMENTE no contexto abaixo. Voce PODE complementar com seu conhecimento geral, desde que diferencie claramente a origem da informacao.

## Regras
- Se o contexto tiver informacoes suficientes: responda usando-as como base, citando as fontes naturalmente
- Se o contexto for parcial: responda o que puder + indique o que ficou sem cobertura
- Se o contexto for irrelevante/vazio: diga "A base de conhecimento nao possui informacoes sobre este tema, mas posso responder com conhecimento geral" e responda
- NUNCA invente informacoes que contradigam o contexto
- Use formatacao leve (paragrafos, bullets) para legibilidade
- Responda SEMPRE em portugues brasileiro

<contexto>
{context}
</contexto>"""


class RagSintese:
    """Faz sintese RAG montando o prompt com os fragmentos e chamando o LLM."""

    def __init__(self):
        self.repo = RagRepository()

    def consultar(self, pergunta: str, limite: int = 5, spotify_id: str = None) -> dict:
        """
        Busca fragmentos similares e gera uma resposta sintetizada.
        Retorna a resposta + as fontes utilizadas.
        Se spotify_id for informado, respeita o provider do usuario.
        """
        fragmentos = self.repo.buscar_similares(pergunta, limite)
        if not fragmentos:
            return {
                "resposta": None,
                "usou_rag": False,
                "fontes":   [],
                "fragmentos": [],
            }

        contexto = "\n\n---\n\n".join(f.conteudo for f in fragmentos)
        system_prompt = SYSTEM_PROMPT_SINTESE.format(context=contexto)

        if spotify_id:
            from app.llm_provider.service import get_llm_for_sintese
            llm = get_llm_for_sintese(spotify_id)
        else:
            llm = get_llm()
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=pergunta),
            ]
            resposta = llm.invoke(messages)
            if hasattr(resposta, "content"):
                resposta = resposta.content
        except Exception:
            logger.exception("Erro na sintese RAG")
            return {
                "resposta": None,
                "usou_rag": True,
                "fontes":   [],
                "fragmentos": [{"fragmento_id": f.id, "documento_id": f.documento_id, "conteudo": f.conteudo[:300]} for f in fragmentos],
            }

        return {
            "resposta":   resposta,
            "usou_rag":   True,
            "fontes":     [{"fragmento_id": f.id, "conteudo": f.conteudo[:200]} for f in fragmentos],
            "fragmentos": [{"fragmento_id": f.id, "documento_id": f.documento_id, "conteudo": f.conteudo} for f in fragmentos],
        }