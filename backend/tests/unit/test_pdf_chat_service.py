import os
from unittest.mock import ANY, Mock, call, patch

import pytest
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.llms import FakeListLLM

from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import InMemoryDocumentStore
from repositories.vector_db import InMemoryStore
from services.pdf_chat_service import PDFChatService


@pytest.fixture(autouse=True)
def mock_openai_dependencies():
    """Mock OpenAI dependencies with fake implementations for all tests."""
    os.environ["OPENAI_API_KEY"] = "sk-fake-key-for-testing"

    fake_llm = FakeListLLM(responses=["This is a test response"])
    mock_chat = Mock(spec=ChatOpenAI)

    with patch("langchain_openai.OpenAI", return_value=fake_llm), patch(
        "brain.model_router.ChatOpenAI", return_value=mock_chat
    ), patch(
        "langchain_community.chat_message_histories.PostgresChatMessageHistory"
    ) as mock_history:
        # Setup mock history
        mock_history.return_value.messages = []
        mock_history.return_value.add_user_message = Mock()
        mock_history.return_value.add_ai_message = Mock()
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
def vector_store():
    """Create an InMemoryStore instance for testing."""
    return InMemoryStore(embeddings=FakeEmbeddings(size=1536))


@pytest.fixture
def document_store():
    """Create an InMemoryDocumentStore instance for testing."""
    return InMemoryDocumentStore()


@pytest.fixture
def pdf_chat_service(mock_chains, vector_store, document_store):
    """Create a PDFChatService instance for testing."""
    mock_rag_chain, mock_summary_chain = mock_chains
    return PDFChatService(
        vector_store=vector_store,
        document_store=document_store,
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
    def test_pdf_upload_adds_to_vector_store(self, pdf_chat_service, pdf_path):
        """Test that PDF upload adds documents to both document store and vector store."""
        session_id = "test_session"
        result = pdf_chat_service.upload(pdf_path, session_id)
        doc_id = result["doc_id"]

        # Verify document is stored
        full_text = pdf_chat_service.document_store.get_document(doc_id)
        assert full_text is not None

        # Get retriever for the specific session and doc
        retriever = pdf_chat_service.vector_store.get_retriever(session_id, doc_id)
        assert retriever is not None

        # Verify documents are retrievable
        docs = retriever.get_relevant_documents("test query")
        assert len(docs) > 0

        # Verify metadata is correctly set
        assert all(
            doc.metadata.get("session_id") == session_id
            and doc.metadata.get("doc_id") == doc_id
            for doc in docs
        )

    def test_basic_query(self, loaded_pdf_chat_service):
        """Test querying the PDF content."""
        service, session_id, doc_id = loaded_pdf_chat_service

        # Create mock router response just for this test
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        service.router = mock_router

        response = service.query(
            session_id=session_id,
            doc_id=doc_id,
            question="What is this document about?",
        )
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_summary_query(self, loaded_pdf_chat_service):
        """Test summary functionality."""
        service, session_id, doc_id = loaded_pdf_chat_service

        # Create mock router response for summary
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="summary")
        service.router = mock_router

        response = service.query(
            session_id=session_id,
            doc_id=doc_id,
            question="Summarize this document",
        )

        assert response == "Mock summary response"
        service.summary_chain.run.assert_called_once()

    def test_chat_history_integration(self, loaded_pdf_chat_service):
        """Test chat history integration with PostgresChatMessageHistory."""
        service, session_id, doc_id = loaded_pdf_chat_service

        # Create mock router response for Q&A
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        service.router = mock_router

        # Mock PostgresChatMessageHistory before making any calls
        with patch(
            "services.pdf_chat_service.PostgresChatMessageHistory"
        ) as mock_history_cls:
            mock_history = Mock()
            mock_history.messages = []
            mock_history.add_user_message = Mock()
            mock_history.add_ai_message = Mock()
            mock_history_cls.return_value = mock_history

            # First question
            response1 = service.query(
                session_id=session_id,
                doc_id=doc_id,
                question="What is the main topic?",
            )

            # Follow-up question
            response2 = service.query(
                session_id=session_id,
                doc_id=doc_id,
                question="Can you elaborate?",
            )

            # Verify responses
            assert response1 == "Mock RAG response"
            assert response2 == "Mock RAG response"

            # Verify chat history was updated correctly
            assert mock_history.add_user_message.call_count == 2
            assert mock_history.add_ai_message.call_count == 2

            # Verify the correct messages were added in order
            mock_history.add_user_message.assert_has_calls(
                [call("What is the main topic?"), call("Can you elaborate?")]
            )
            mock_history.add_ai_message.assert_has_calls(
                [call("Mock RAG response"), call("Mock RAG response")]
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

        with patch(
            "services.pdf_chat_service.PostgresChatMessageHistory"
        ) as mock_history_cls:
            # Setup separate mock histories for each document
            histories = {}
            histories[f"{session_id}:{doc_1_id}"] = Mock(name=f"history_{doc_1_id}")
            histories[f"{session_id}:{doc_2_id}"] = Mock(name=f"history_{doc_2_id}")

            for history in histories.values():
                history.messages = []
                history.add_user_message = Mock()
                history.add_ai_message = Mock()

            # Configure mock to return different histories based on session_id:doc_id
            def get_mock_history(connection_string, session_id):
                print(f"Getting history for session {session_id}")
                history = histories.get(session_id)
                if not history:
                    raise ValueError(f"No history found for session {session_id}")
                return history

            mock_history_cls.side_effect = get_mock_history

            # Query first document
            response1 = pdf_chat_service.query(
                session_id=session_id,
                doc_id=doc_1_id,
                question="What is document 1 about?",
            )

            # Query second document
            response2 = pdf_chat_service.query(
                session_id=session_id,
                doc_id=doc_2_id,
                question="What is document 2 about?",
            )

            # Verify both documents are accessible and queryable
            assert response1 == "Mock RAG response"
            assert response2 == "Mock RAG response"

            # Verify documents are stored separately
            doc1_content = pdf_chat_service.document_store.get_document(doc_1_id)
            doc2_content = pdf_chat_service.document_store.get_document(doc_2_id)
            assert doc1_content is not None
            assert doc2_content is not None
            assert (
                doc1_content == doc2_content
            )  # As we are using the same file, the content should be the same

            # Print debug info
            history1 = histories[f"{session_id}:{doc_1_id}"]
            history2 = histories[f"{session_id}:{doc_2_id}"]
            print(f"\nHistory 1 ({doc_1_id}) calls:", history1.mock_calls)
            print(f"History 2 ({doc_2_id}) calls:", history2.mock_calls)

            # Verify chat histories were kept separate
            assert (
                history1.add_user_message.call_count == 1
            ), "History 1 should have exactly 1 message"
            assert (
                history2.add_user_message.call_count == 1
            ), "History 2 should have exactly 1 message"
            history1.add_user_message.assert_called_once_with(
                "What is document 1 about?"
            )
            history2.add_user_message.assert_called_once_with(
                "What is document 2 about?"
            )
