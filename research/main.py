import os

import yaml

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from rag import create_rag_chain
from router import create_router
from summariser import create_summary_chain
from document_processing import load_pdf, chunk_docs

with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

file_path = os.path.join(os.path.dirname(__file__), config['DOCS_DIR'], config['TEST_FILE'])

def create_db(docs: list) -> FAISS:
    """Create a FAISS database from a list of documents."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    db = FAISS.from_documents(docs, embeddings)
    return db

def create_retriever(db: FAISS) -> FAISS:
    """Create a retriever from a FAISS database."""
    retriever = db.as_retriever(search_kwargs={'k': 3})
    return retriever


if __name__ == "__main__":
    print("Hello, World!")

    pages = load_pdf(file_path)
    docs = chunk_docs(pages)
    
    db = create_db(docs)
    retriever = create_retriever(db)

    rag_chain = create_rag_chain(retriever)

    
    router = create_router()

    query = input("Enter a question: ")
    result = router.invoke(query)
    
    if result.task.lower() == "q_and_a":
        result = rag_chain.invoke(query)
    elif result.task.lower() == "summary":
        full_text = "\n".join([page.page_content for page in pages])
        document = [Document(page_content=full_text, metadata={})]

        # Create and use the summary chain
        summary_chain = create_summary_chain()
        result = summary_chain.invoke({"context": document})
    else:
        print("Invalid task")

    print(result)
