from abc import ABC, abstractmethod
from typing import Dict, List

from langchain.schema import Document
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.vectorstores.in_memory import InMemoryVectorStore


class VectorStore(ABC):
    """Abstract base class for vector stores with session and document filtering."""

    @abstractmethod
    def add_documents(
        self, documents: List[Document], session_id: str, doc_id: str
    ) -> None:
        """Add documents to the vector store with session and document identifiers."""
        pass

    @abstractmethod
    def get_retriever(self, session_id: str, doc_id: str) -> VectorStoreRetriever:
        """Get a retriever that filters by session and document."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all documents from the store."""
        pass


class InMemoryStore(VectorStore):
    """In-memory vector store implementation with filtering."""

    def __init__(self, embeddings: Embeddings):
        self.store = InMemoryVectorStore(embeddings)
        self.docs_metadata: Dict[str, Document] = (
            {}
        )  # Track document metadata for filtering

    def add_documents(
        self, documents: List[Document], session_id: str, doc_id: str
    ) -> None:
        """Add documents to the vector store with session and document identifiers."""
        for doc in documents:
            doc.metadata["session_id"] = session_id
            doc.metadata["doc_id"] = doc_id

        self.store.add_documents(documents)

    def get_retriever(self, session_id: str, doc_id: str) -> VectorStoreRetriever:
        """Retrieve documents from the vector store that match the session and doc identifiers."""

        def filter_fn(doc: Document) -> bool:
            return (
                doc.metadata.get("session_id") == session_id
                and doc.metadata.get("doc_id") == doc_id
            )

        return self.store.as_retriever(
            search_kwargs={
                "filter": filter_fn,
                "k": 4,  # Number of relevant chunks to retrieve
            }
        )

    def clear(self) -> None:
        """Reset both store and metadata"""
        self.store = InMemoryVectorStore(self.store._embedding)
        self.docs_metadata.clear()


class PGVectorStore(VectorStore):
    """Postgres vector store implementation with filtering."""

    def __init__(
        self,
        embeddings: Embeddings,
        connection_string: str,
        collection_name: str = "documents",
    ):
        self.store = PGVector(
            embedding_function=embeddings,
            connection_string=connection_string,
            collection_name=collection_name,
        )

    def add_documents(
        self, documents: List[Document], session_id: str, doc_id: str
    ) -> None:
        """Add documents to the vector store with session and document identifiers."""
        for doc in documents:
            doc.metadata["session_id"] = session_id
            doc.metadata["doc_id"] = doc_id

        self.store.add_documents(documents)

    def get_retriever(self, session_id: str, doc_id: str) -> VectorStoreRetriever:
        return self.store.as_retriever(
            search_kwargs={
                "filter": {"session_id": session_id, "doc_id": doc_id},
                "k": 4,  # Number of relevant chunks to retrieve
            }
        )

    def clear(self) -> None:
        """Clear all documents from the collection"""
        self.store.delete_collection()
