from pathlib import Path
from unittest.mock import Mock

import pytest
from langchain_openai import ChatOpenAI

from services.pdf_chat_service import PDFChatService


@pytest.fixture
def pdf_path():
    """Returns the path to the Bitcoin whitepaper PDF."""

    current_dir = Path(__file__).parent.parent  # goes up one level from tests/
    pdf_path = (
        current_dir / "docs" / "Bitcoin - A Peer-to-Peer Electronic Cash System.pdf"
    )

    if not pdf_path.exists():
        raise FileNotFoundError(f"Test PDF not found at {pdf_path}")

    return str(pdf_path)
