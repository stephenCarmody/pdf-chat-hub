import logging
from typing import Annotated

from fastapi import Depends
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

logger = logging.getLogger(__name__)


class Services:
    def __init__(self):
        self.document_store: DocumentStore | None = None
        self.vector_store: VectorStore | None = None


# Create a single instance to hold our services
services = Services()


def get_vector_store() -> VectorStore:
    """Get's the correct vector store implementation based on the environment."""
    if services.vector_store is None:
        embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        if settings.use_postgres_db:
            services.vector_store = PGVectorStore(
                embeddings=embeddings,
                connection_string=settings.connection_string,
            )
        else:
            services.vector_store = InMemoryVectorStore(embeddings=embeddings)

    return services.vector_store


def get_document_store() -> DocumentStore:
    """Get's the correct document store implementation based on the environment."""
    if services.document_store is None:
        DOCUMENT_STORES = {
            "s3": S3DocumentStore,
            "in_memory": InMemoryDocumentStore,
            "postgres": PostgresDocumentStore,
        }
        logger.info(f"Using document store type: {settings.document_store_type}")
        services.document_store = DOCUMENT_STORES[settings.document_store_type]()

    return services.document_store


def get_pdf_service(
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
    document_store: Annotated[DocumentStore, Depends(get_document_store)],
) -> PDFChatService:
    """Dependency provider for PDFChatService"""
    return PDFChatService(
        document_processor=DocumentProcessor(),
        vector_store=vector_store,
        document_store=document_store,
        rag_chain=RAGChain(),
        summary_chain=SummaryChain(),
    )
