from typing import Optional
from services.pdf_chat_service import PDFChatService

def get_pdf_service() -> PDFChatService:
    """Dependency provider for PDFChatService"""
    return PDFChatService()
