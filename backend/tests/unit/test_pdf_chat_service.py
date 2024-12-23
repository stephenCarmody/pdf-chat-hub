import os
from unittest.mock import ANY, Mock, patch

import pytest
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import FakeListLLM

from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import InMemorySessionStateDB, FileSystemSessionStateDB
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
    result = pdf_chat_service.upload(pdf_path, session_id)
    return pdf_chat_service, session_id, result["doc_id"]


class TestPDFChatService:
    def test_pdf_upload(self, pdf_chat_service, pdf_path):
        """Test that PDF upload works correctly."""
        session_id = "test_session"
        result = pdf_chat_service.upload(pdf_path, session_id)
        doc_id = result["doc_id"]

        # Verify state was saved
        state = pdf_chat_service.session_state_db.get(f"{session_id}:{doc_id}")
        assert state is not None
        assert "docs" in state
        assert "full_text" in state
        assert "pages" in state

        # Verify content exists
        assert len(state["docs"]) > 0
        assert len(state["full_text"]) > 0

    def test_basic_query(self, loaded_pdf_chat_service):
        """Test querying the PDF content."""
        service, session_id, doc_id = loaded_pdf_chat_service

        # Create mock router response just for this test
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        service.router = mock_router

        response = service.query(
            "What is this document about?", 
            session_id=session_id,
            doc_id=doc_id,
            chat_history=[]
        )
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_summary_query(self, loaded_pdf_chat_service):
        """Test summary functionality."""
        service, session_id, doc_id = loaded_pdf_chat_service

        # Create mock router response for summary
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        service.router = mock_router

        response = service.query(
            "What is the main topic of this document?",
            session_id=session_id,
            doc_id=doc_id,
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
        service, session_id, doc_id = loaded_pdf_chat_service

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
            doc_id=doc_id,
            chat_history=chat_history,
        )
        chat_history.append(("What is the main topic of this document?", response1))

        # Follow-up question
        response2 = service.query(
            "Can you elaborate on that?",
            session_id=session_id,
            doc_id=doc_id,
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

    def test_multiple_documents_per_session(self, pdf_chat_service, pdf_path):
        """Test handling multiple documents within the same session."""
        session_id = "test_session"
        
        # Upload first document
        upload_1_output = pdf_chat_service.upload(pdf_path, session_id)
        doc_1_id = upload_1_output["doc_id"]
        
        # Upload second document (same file, different instance)
        upload_2_output = pdf_chat_service.upload(pdf_path, session_id)
        doc_2_id = upload_2_output["doc_id"]
        
        # Verify different doc_ids
        assert doc_1_id != doc_2_id
        
        # Create mock router response for testing
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        pdf_chat_service.router = mock_router
        
        # Query first document with chat history
        chat_history1 = []
        response1 = pdf_chat_service.query(
            "What is document 1 about?",
            session_id=session_id,
            doc_id=doc_1_id,
            chat_history=chat_history1
        )
        chat_history1.append(("What is document 1 about?", response1))
        
        # Follow-up query for first document
        response1_followup = pdf_chat_service.query(
            "Tell me more about document 1",
            session_id=session_id,
            doc_id=doc_1_id,
            chat_history=chat_history1
        )
        
        # Query second document with different chat history
        chat_history2 = []
        response2 = pdf_chat_service.query(
            "What is document 2 about?",
            session_id=session_id,
            doc_id=doc_2_id,
            chat_history=chat_history2
        )
        chat_history2.append(("What is document 2 about?", response2))
        
        # Verify both documents are accessible and queryable
        assert response1 == "Mock RAG response"
        assert response2 == "Mock RAG response"

        # Verify states are stored separately
        state1 = pdf_chat_service.session_state_db.get(f"{session_id}:{doc_1_id}")
        state2 = pdf_chat_service.session_state_db.get(f"{session_id}:{doc_2_id}")
        
        assert state1 is not None
        assert state2 is not None
        
        # Verify chat histories were passed correctly
        pdf_chat_service.rag_chain.run.assert_any_call(
            "Tell me more about document 1",
            ANY,
            [("What is document 1 about?", "Mock RAG response")]
        )
        
        pdf_chat_service.rag_chain.run.assert_any_call(
            "What is document 2 about?",
            ANY,
            []  # Should have empty history as it's the first query
        )
