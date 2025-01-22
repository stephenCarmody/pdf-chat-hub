import os
from pathlib import Path

import pytest
from langchain_community.embeddings import FakeEmbeddings

from brain.document_processing import chunk_docs, load_pdf
from repositories.vector_db import PGVectorStore
from settings import settings


@pytest.fixture
def vector_store():
    """Fixture that creates and tears down a vector store"""
    store = PGVectorStore(
        embeddings=FakeEmbeddings(size=1536),  # Same dimension as OpenAI embeddings
        connection_string=settings.connection_string,
        collection_name="test_documents",
    )
    yield store
    store.clear()


@pytest.fixture
def bitcoin_chunks():
    """Fixture that loads and chunks the Bitcoin whitepaper"""
    # Load the PDF
    docs_folder = Path(__file__).parent.parent.parent / "docs"
    pages = load_pdf(
        os.path.join(docs_folder, "Bitcoin - A Peer-to-Peer Electronic Cash System.pdf")
    )
    documents = chunk_docs(pages)
    return documents


@pytest.mark.integration
def test_add_documents_to_vector_store(vector_store, bitcoin_chunks):
    """Test adding document chunks to the vector store"""
    # GIVEN chunks from the Bitcoin whitepaper
    session_id = "test-session"
    doc_id = "bitcoin-whitepaper"

    # WHEN we add the documents to the vector store
    vector_store.add_documents(bitcoin_chunks, session_id, doc_id)

    # THEN we can retrieve them using the same session and doc id
    retriever = vector_store.get_retriever(session_id, doc_id)
    results = retriever.get_relevant_documents("What is Bitcoin?")

    # Verify we got results back
    assert len(results) > 0
    # Verify metadata is correctly set
    assert all(doc.metadata["session_id"] == session_id for doc in results)
    assert all(doc.metadata["doc_id"] == doc_id for doc in results)


@pytest.mark.integration
def test_similarity_search(vector_store, bitcoin_chunks):
    """Test similarity search functionality"""
    # GIVEN documents are stored in the vector store
    session_id = "test-session"
    doc_id = "bitcoin-whitepaper"
    vector_store.add_documents(bitcoin_chunks, session_id, doc_id)

    # WHEN we perform similarity searches with different queries
    retriever = vector_store.get_retriever(session_id, doc_id)

    # Test technical query
    technical_results = retriever.get_relevant_documents(
        "How does the proof of work system function?"
    )

    # Test conceptual query
    conceptual_results = retriever.get_relevant_documents(
        "What problem does Bitcoin solve?"
    )
    # THEN we get relevant chunks back
    assert len(technical_results) == 4  # Based on k=4 in vector_db.py
    assert len(conceptual_results) == 4

    # AND the results are different for different queries
    assert technical_results != conceptual_results

    # AND each result has the correct metadata
    for doc in technical_results + conceptual_results:
        assert doc.metadata["session_id"] == session_id
        assert doc.metadata["doc_id"] == doc_id
        assert isinstance(doc.page_content, str)
        assert len(doc.page_content) > 0
