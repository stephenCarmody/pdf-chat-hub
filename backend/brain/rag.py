from typing import Dict, List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


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

    def run(self, query: str, retriever: FAISS, chat_history: List[Tuple[str, str]]):
        # Create the chain at runtime with the provided retriever
        chain = (
            {
                "context": lambda x: self._combine_documents(
                    retriever.invoke(x["question"])
                ),
                "chat_history": lambda x: self._format_chat_history(x["chat_history"]),
                "question": lambda x: x["question"],
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        return chain.invoke({"question": query, "chat_history": chat_history})

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """Format chat history into a string."""
        if not chat_history:
            return "No previous conversation."

        formatted_messages = []
        for msg in chat_history:
            prefix = "Human" if msg.role == "user" else "Assistant"
            formatted_messages.append(f"{prefix}: {msg.content}")

        return "\n".join(formatted_messages)

    def _combine_documents(self, docs):
        """Combine multiple documents into a single string."""
        return "\n\n".join([doc.page_content for doc in docs])
