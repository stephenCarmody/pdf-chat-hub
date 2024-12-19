from abc import ABC, abstractmethod

from langchain.schema import Document
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


class VectorDBFactory(ABC):
    @abstractmethod
    def create_db(self, docs: list[Document], k: int = 3) -> FAISS:
        """Create a vector database from documents and return it as a retriever."""
        pass


class OpenAIVectorDBFactory(VectorDBFactory):
    def create_db(self, docs: list[Document], k: int = 3) -> FAISS:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        db = FAISS.from_documents(docs, embeddings)
        return db.as_retriever(search_kwargs={"k": k})


class FakeVectorDBFactory(VectorDBFactory):
    def create_db(self, docs: list[Document], k: int = 3) -> FAISS:
        embeddings = FakeEmbeddings(size=1536)
        db = FAISS.from_documents(docs, embeddings)
        return db.as_retriever(search_kwargs={"k": k})
