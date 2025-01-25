import os
from unittest.mock import ANY, Mock, patch

import pytest
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.llms import FakeListLLM
from langchain_core.messages import AIMessage, HumanMessage

from brain.document_processing import DocumentProcessor
from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import InMemoryDocumentStore
from repositories.vector_db import PGVectorStore
from services.pdf_chat_service import PDFChatService
from settings import settings


@pytest.fixture(scope="module")
def connection_string():
    """Get the connection string for the test database."""
    return settings.connection_string


@pytest.fixture(scope="module")
def test_pdf_path():
    """Create a module-scoped fixture for the test PDF path."""
    return "docs/Bitcoin - A Peer-to-Peer Electronic Cash System.pdf"


@pytest.fixture(scope="module")
def vector_store(connection_string):
    """Create a real PGVector store instance for testing."""
    embeddings = FakeEmbeddings(size=settings.embedding_size)
    store = PGVectorStore(
        embeddings=embeddings,
        connection_string=connection_string,
        collection_name="test_documents",
    )
    yield store
    # Cleanup
    store.clear()


@pytest.fixture(scope="module")
def document_store():
    """Create an in-memory document store for testing."""
    return InMemoryDocumentStore()


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
def mock_chains(mock_openai_dependencies):
    """Create mock RAG and Summary chains."""
    mock_rag_chain = Mock(spec=RAGChain)
    mock_rag_chain.run.return_value = "Mock RAG response"

    mock_summary_chain = Mock(spec=SummaryChain)
    mock_summary_chain.run.return_value = "Mock summary response"

    return mock_rag_chain, mock_summary_chain


@pytest.fixture(scope="module")
def pdf_chat_service(mock_chains, vector_store, document_store):
    """Create a PDFChatService instance for testing."""
    mock_rag_chain, mock_summary_chain = mock_chains
    return PDFChatService(
        document_processor=DocumentProcessor(),
        vector_store=vector_store,
        document_store=document_store,
        rag_chain=mock_rag_chain,
        summary_chain=mock_summary_chain,
    )


@pytest.fixture(scope="module")
def loaded_pdf_chat_service(pdf_chat_service, test_pdf_path):
    """Create a PDFChatService instance with a loaded PDF."""
    session_id = "test_integration_session"
    result = pdf_chat_service.upload(test_pdf_path, session_id)
    return pdf_chat_service, session_id, result["doc_id"]


@pytest.mark.integration
class TestPDFChatServiceIntegration:
    def test_end_to_end_chat_flow(self, loaded_pdf_chat_service):
        """Test the complete chat flow using real Postgres for chat history and vector store."""
        service, session_id, doc_id = loaded_pdf_chat_service

        # Create mock router response for testing
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        service.router = mock_router

        # First question
        response1 = service.query(
            session_id=session_id,
            doc_id=doc_id,
            question="What is this document about?",
        )
        assert response1 == "Mock RAG response"

        # Follow-up question should have access to chat history from Postgres
        response2 = service.query(
            session_id=session_id,
            doc_id=doc_id,
            question="Can you elaborate on that?",
        )
        assert response2 == "Mock RAG response"

        # Verify the RAG chain was called with the correct history
        service.rag_chain.run.assert_any_call(
            "Can you elaborate on that?",
            ANY,  # retriever
            [
                HumanMessage(content="What is this document about?"),
                AIMessage(content="Mock RAG response"),
            ],
        )

    def test_multiple_documents_with_shared_history(
        self, pdf_chat_service, test_pdf_path
    ):
        """Test handling multiple documents with real chat history storage."""
        session_id = "test_integration_multi_doc"

        # Upload two documents
        result1 = pdf_chat_service.upload(test_pdf_path, session_id)
        result2 = pdf_chat_service.upload(test_pdf_path, session_id)
        doc_1_id = result1["doc_id"]
        doc_2_id = result2["doc_id"]

        # Create mock router response
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="q_and_a")
        pdf_chat_service.router = mock_router

        # Query first document
        response1 = pdf_chat_service.query(
            session_id=session_id,
            doc_id=doc_1_id,
            question="Tell me about document 1",
        )
        assert response1 == "Mock RAG response"

        # Query second document
        response2 = pdf_chat_service.query(
            session_id=session_id,
            doc_id=doc_2_id,
            question="Tell me about document 2",
        )
        assert response2 == "Mock RAG response"

        # Follow-up question for first document should only see its history
        response3 = pdf_chat_service.query(
            session_id=session_id,
            doc_id=doc_1_id,
            question="Can you elaborate on document 1?",
        )
        assert response3 == "Mock RAG response"

        # Verify RAG chain was called with correct history for each document
        pdf_chat_service.rag_chain.run.assert_any_call(
            "Can you elaborate on document 1?",
            ANY,  # retriever
            [
                HumanMessage(content="Tell me about document 1"),
                AIMessage(content="Mock RAG response"),
            ],
        )

    def test_vector_search_integration(self, loaded_pdf_chat_service):
        """Test vector search functionality with real PGVector store."""
        service, session_id, doc_id = loaded_pdf_chat_service

        # Get retriever for the specific session and doc
        retriever = service.vector_store.get_retriever(session_id, doc_id)

        # Test actual vector similarity search
        docs = retriever.get_relevant_documents("test query")

        # Verify we got results and metadata is correct
        assert len(docs) > 0
        assert all(
            doc.metadata.get("session_id") == session_id
            and doc.metadata.get("doc_id") == doc_id
            for doc in docs
        )

    def test_summary_with_real_document_storage(self, loaded_pdf_chat_service):
        """Test summary functionality with real document storage."""
        service, session_id, doc_id = loaded_pdf_chat_service

        # Create mock router response for summary
        mock_router = Mock()
        mock_router.invoke.return_value = Mock(task="summary")
        service.router = mock_router

        # Request summary
        response = service.query(
            session_id=session_id,
            doc_id=doc_id,
            question="Summarize this document",
        )

        assert response == "Mock summary response"

        # Verify the document content was retrieved correctly
        doc_content = service.document_store.get_document(doc_id)
        assert doc_content is not None
        assert len(doc_content) > 0
