import os

from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings

from brain.document_processing import DocumentProcessor
from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import (
    DocumentStore,
    InMemoryDocumentStore,
    PostgresDocumentStore,
    S3DocumentStore,
)
from repositories.vector_db import InMemoryVectorStore, PGVectorStore
from services.pdf_chat_service import PDFChatService
from settings import settings


def get_vector_store() -> VectorStore:
    """Get's the correct vector store implementation based on the environment."""
    embeddings = OpenAIEmbeddings(model=settings.embedding_model)

    if settings.use_postgres_db:
        return PGVectorStore(
            embeddings=embeddings,
            connection_string=settings.connection_string,
        )
    else:
        return InMemoryVectorStore(embeddings=embeddings)


def get_document_store() -> DocumentStore:
    """Get's the correct document store implementation based on the environment."""
    DOCUMENT_STORES = {
        "s3": S3DocumentStore,
        "in_memory": InMemoryDocumentStore,
        "postgres": PostgresDocumentStore,
    }
    return DOCUMENT_STORES[settings.document_store_type]()


def get_pdf_service() -> PDFChatService:
    """Dependency provider for PDFChatService"""
    return PDFChatService(
        document_processor=DocumentProcessor(),
        vector_store=get_vector_store(),
        document_store=get_document_store(),
        rag_chain=RAGChain(),
        summary_chain=SummaryChain(),
    )
