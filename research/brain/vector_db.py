from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


def create_db(docs: list) -> FAISS:
    """Create a FAISS database from a list of documents."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    db = FAISS.from_documents(docs, embeddings)
    return db


def create_retriever(db: FAISS) -> FAISS:
    """Create a retriever from a FAISS database."""
    retriever = db.as_retriever(search_kwargs={"k": 3})
    return retriever
