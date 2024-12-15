from typing import Optional
from services.pdf_chat_service import PDFChatService

def get_pdf_service(session_id: Optional[str] = None) -> PDFChatService:
    """Dependency provider for PDFChatService"""
    return PDFChatService(session_id=session_id)
