from io import BytesIO

from langchain.schema import Document

from brain.document_processing import chunk_docs, load_pdf
from brain.model_router import create_router
from brain.rag import create_rag_chain
from brain.summariser import create_summary_chain
from brain.vector_db import create_db, create_retriever


class PDFChatService:
    def __init__(self):
        self.pages = None
        self.rag_chain = None
        self.summary_chain = None
        self.full_text_doc = None
        self.router = create_router()

    def query(self, query: str):
        """
        Query the document with a question / task.
        """
        if not self.rag_chain or not self.summary_chain:
            return "Please upload a document first."

        result = self.router.invoke(query)

        if result.task.lower() == "q_and_a":
            result = self.rag_chain.invoke(query)
        elif result.task.lower() == "summary":
            result = self.summary_chain.invoke({"context": self.full_text_doc})
        else:
            return "Invalid task"

        return result

    def upload(self, file_path: str) -> None:
        """
        Upload a PDF file to the service. Resets the chat history.
        """
        try:
            self.pages = load_pdf(file_path)
            docs = chunk_docs(self.pages)

            # Prepare full text document for summarization
            full_text = "\n".join([page.page_content for page in self.pages])
            self.full_text_doc = [Document(page_content=full_text, metadata={})]

            # Create vector DB and chains
            db = create_db(docs)
            retriever = create_retriever(db)
            self.rag_chain = create_rag_chain(retriever)
            self.summary_chain = create_summary_chain()
        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}")
