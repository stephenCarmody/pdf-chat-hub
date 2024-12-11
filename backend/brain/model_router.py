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


def create_router():
    """Create a router that directs user queries to appropriate actions.

    Returns:
        A router chain that processes queries and returns structured output.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(RouteQuery)

    system_prompt = """You are an expert at routing user queries to the most relevant task/action.

    You will be given a user query and you will need to determine which task/action is most relevant to answer the user's question.
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{query}")]
    )

    router = prompt | structured_llm
    return router
