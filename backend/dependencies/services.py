from typing import Optional

from langchain_openai import OpenAIEmbeddings

from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import FileSystemSessionStateDB
from repositories.vector_db import InMemoryVectorStore
from services.pdf_chat_service import PDFChatService


def get_pdf_service() -> PDFChatService:
    """Dependency provider for PDFChatService"""
    # TODO implement strategy pattern to create different one if local vs prod
    return PDFChatService(
        vector_store=InMemoryVectorStore(
            embeddings=OpenAIEmbeddings(model="text-embedding-3-large")
        ),
        session_state_db=FileSystemSessionStateDB(),
        rag_chain=RAGChain(),
        summary_chain=SummaryChain(),
    )
