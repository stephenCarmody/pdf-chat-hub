from typing import Optional

from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import FileSystemSessionStateDB
from repositories.vector_db import OpenAIVectorDBFactory
from services.pdf_chat_service import PDFChatService


def get_pdf_service() -> PDFChatService:
    """Dependency provider for PDFChatService"""
    # TODO implement strategy pattern to create different one if local vs prod
    return PDFChatService(
        vector_db_factory=OpenAIVectorDBFactory(),
        session_state_db=FileSystemSessionStateDB(),
        rag_chain=RAGChain(),
        summary_chain=SummaryChain(),
    )
