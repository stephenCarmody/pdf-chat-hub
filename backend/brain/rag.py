from typing import List

from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from repositories.vector_db import VectorStoreRetriever


class RAGChain:
    def __init__(self):
        self.template = """
        Answer the question based on the following document and chat history.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        If the user speaks to you as if you are a human, respond as if you are a human.
        If the user asks about previous messages, use the chat history to answer the question.
        
        Context: {context}
        
        Chat History:
        {chat_history}
        
        Current Question: {question}
        """
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def run(
        self,
        query: str,
        retriever: VectorStoreRetriever,
        messages: List,
    ):
        # Create the chain at runtime with the provided retriever
        chain = (
            {
                "context": lambda x: self._combine_documents(
                    retriever.invoke(x["question"])
                ),
                "chat_history": lambda x: self._format_messages(x["chat_history"]),
                "question": lambda x: x["question"],
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        return chain.invoke({"question": query, "chat_history": messages})

    def _format_messages(self, messages: List) -> str:
        """Format messages from PostgresChatMessageHistory."""
        if not messages:
            return "No previous conversation."
        return "\n".join([f"{msg.type}: {msg.content}" for msg in messages])

    def _combine_documents(self, docs):
        """Combine multiple documents into a single string."""
        return "\n\n".join([doc.page_content for doc in docs])
