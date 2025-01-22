import os
from langchain_openai import OpenAIEmbeddings

from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import FileSystemSessionStateDB
from repositories.vector_db import InMemoryVectorStore, PGVectorStore
from services.pdf_chat_service import PDFChatService

from langchain_core.vectorstores import VectorStore

from settings import settings

def get_vector_store() -> VectorStore:
    """Get's the correct vector store implementation based on the environment."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    
    if settings.use_postgres_db:
        return PGVectorStore(
            embeddings=embeddings,
            connection_string=settings.connection_string,
        )
    else:
        return InMemoryVectorStore(embeddings=embeddings)


def get_pdf_service() -> PDFChatService:
    """Dependency provider for PDFChatService"""
    return PDFChatService(
        vector_store=get_vector_store(),
        session_state_db=FileSystemSessionStateDB(),
        rag_chain=RAGChain(),
        summary_chain=SummaryChain(),
    )
