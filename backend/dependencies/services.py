from typing import Optional

from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.vector_db import VectorDBFactory
from repositories.session_db import InMemorySessionStateDB
from services.pdf_chat_service import PDFChatService


def get_pdf_service() -> PDFChatService:
    """Dependency provider for PDFChatService"""
    return PDFChatService(
        vector_db_factory=VectorDBFactory(),
        session_state_db=InMemorySessionStateDB(),
        rag_chain=RAGChain(),
        summary_chain=SummaryChain(),
    )
