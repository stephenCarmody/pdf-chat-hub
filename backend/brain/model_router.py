from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class RouteQuery(BaseModel):
    """Route a user query to the most relevant task/action."""

    task: Literal["q_and_a", "summary"] = Field(
        ...,
        description="Given a user question choose which action would be most relevant for answering their question",
    )


# TODO: Could this be a class or would it be overkill ?
def create_router():
    """Create a router that directs user queries to appropriate actions.

    Returns:
        A router chain that processes queries and returns structured output.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(RouteQuery)

    system_prompt = """You are an expert at routing user queries to the most relevant task/action.

    You will be given a user query and must route it to one of these tasks:
    - "q_and_a": For specific questions about the paper's content or chat history
    - "summary": For broad, overview-type questions about the paper's main points

    Routing Rules:
    1. Use "q_and_a" when:
       - The user asks specific questions about details in the paper
       - The user asks about previous chat interactions or history
       - The user wants to fact-check or verify specific information
       - The user asks about specific sections, figures, or citations

    2. Use "summary" when:
       - The user asks about the paper's main findings or conclusions
       - The user wants an overview of the paper's key points
       - The user asks about the general topic or theme
       - The user wants to understand the paper's high-level implications

    Always choose the most specific and relevant task. If in doubt between summary and q_and_a, prefer q_and_a for more accurate responses.
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{query}")]
    )

    router = prompt | structured_llm
    return router
