import os
from unittest.mock import ANY, Mock, patch

import pytest
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import FakeListLLM

from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import InMemorySessionStateDB
from repositories.vector_db import FakeVectorDBFactory
from services.pdf_chat_service import PDFChatService


@pytest.fixture(autouse=True)
def mock_openai_dependencies():
    """Mock OpenAI dependencies with fake implementations for all tests."""
    os.environ["OPENAI_API_KEY"] = "sk-fake-key-for-testing"

    fake_llm = FakeListLLM(responses=["This is a test response"])
    mock_chat = Mock(spec=ChatOpenAI)

    with patch("langchain_openai.OpenAI", return_value=fake_llm), patch(
        "brain.model_router.ChatOpenAI", return_value=mock_chat
    ):
        yield mock_chat

    del os.environ["OPENAI_API_KEY"]


@pytest.fixture
def mock_chains():
    """Create mock RAG and Summary chains."""
    mock_rag_chain = Mock(spec=RAGChain)
    mock_rag_chain.run.return_value = "Mock RAG response"

    mock_summary_chain = Mock(spec=SummaryChain)
    mock_summary_chain.run.return_value = "Mock summary response"

    return mock_rag_chain, mock_summary_chain


@pytest.fixture
def pdf_chat_service(mock_chains):
    """Create a PDFChatService instance for testing."""
    mock_rag_chain, mock_summary_chain = mock_chains
    return PDFChatService(
        vector_db_factory=FakeVectorDBFactory(),
        session_state_db=InMemorySessionStateDB(),
        rag_chain=mock_rag_chain,
        summary_chain=mock_summary_chain,
    )


@pytest.fixture
def loaded_pdf_chat_service(pdf_chat_service, pdf_path):
    """Create a PDFChatService instance with a loaded PDF."""
    session_id = "test_session"
    pdf_chat_service.upload(pdf_path, session_id)
    return pdf_chat_service, session_id


class TestPDFChatService:
    def test_pdf_upload(self, pdf_chat_service, pdf_path):
        """Test that PDF upload works correctly."""
        session_id = "test_session"
        pdf_chat_service.upload(pdf_path, session_id)

        # Verify state was saved
        state = pdf_chat_service.session_state_db.get(session_id)
        assert state is not None
        assert "docs" in state
        assert "full_text" in state
        assert "pages" in state

        # Verify content exists
        assert len(state["docs"]) > 0
        assert len(state["full_text"]) > 0

    def test_basic_query(self, loaded_pdf_chat_service):
        """Test querying the PDF content."""
        service, session_id = loaded_pdf_chat_service

        # Create mock router response just for this test
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        service.router = mock_router  # Replace the router just for this test

        # Test basic query
        response = service.query(
            "What is this document about?", session_id=session_id, chat_history=[]
        )
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_summary_query(self, loaded_pdf_chat_service):
        """Test summary functionality."""
        service, session_id = loaded_pdf_chat_service

        # Create mock router response for summary
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        service.router = mock_router

        response = service.query(
            "What is the main topic of this document?",
            session_id=session_id,
            chat_history=[],
        )

        assert response == "Mock RAG response"
        service.rag_chain.run.assert_called_with(
            "What is the main topic of this document?",
            ANY,
            [],
        )

    def test_chat_history(self, loaded_pdf_chat_service):
        """Test chat history functionality."""
        service, session_id = loaded_pdf_chat_service

        # Create mock router response for Q&A
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        service.router = mock_router

        # Simulate a conversation
        chat_history = []

        # First question
        response1 = service.query(
            "What is the main topic of this document?",
            session_id=session_id,
            chat_history=chat_history,
        )
        chat_history.append(("What is the main topic of this document?", response1))

        # Follow-up question
        response2 = service.query(
            "Can you elaborate on that?",
            session_id=session_id,
            chat_history=chat_history,
        )

        # Verify the calls to rag_chain.run
        assert service.rag_chain.run.call_count == 2

        # Verify first call with empty chat history
        service.rag_chain.run.assert_any_call(
            "What is the main topic of this document?",
            ANY,
            [],
        )

        # Verify second call with updated chat history
        service.rag_chain.run.assert_any_call(
            "Can you elaborate on that?",
            ANY,
            [("What is the main topic of this document?", "Mock RAG response")],
        )
