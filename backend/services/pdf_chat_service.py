import logging
from io import BytesIO
from typing import List, Optional

from langchain.schema import Document

from brain.document_processing import chunk_docs, load_pdf
from brain.model_router import create_router
from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import SessionState, SessionStateDB
from repositories.vector_db import VectorDBFactory

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PDFChatService:
    def __init__(
        self,
        vector_db_factory: VectorDBFactory,
        session_state_db: SessionStateDB,
        rag_chain: RAGChain,
        summary_chain: SummaryChain,
    ):
        logger.info("Initializing PDFChatService")
        self.rag_chain = rag_chain
        self.summary_chain = summary_chain
        self.vector_db_factory = vector_db_factory
        self.session_state_db = session_state_db
        self.router = create_router()

    def query(
        self, query: str, session_id: str, chat_history: Optional[List[str]] = None
    ):
        """
        Query the document with a question / task.
        """
        logger.info(f"Querying with query: {query}, session_id: {session_id}, chat_history: {chat_history}")
        state = self.session_state_db.get(session_id)
        if not state:
            return "Please upload a document first."

        try:
            docs = [
                Document(page_content=doc["content"], metadata=doc["metadata"])
                for doc in state["docs"]
            ]

            vector_db = self.vector_db_factory.create_db(docs)
            result = self.router.invoke(query)

            # Implement strategy pattern
            if result.task.lower() == "q_and_a":
                result = self.rag_chain.run(query, vector_db, chat_history or [])
            elif result.task.lower() == "summary":
                full_text_doc = [Document(page_content=state["full_text"], metadata={})]
                result = self.summary_chain.run(full_text_doc)
            else:
                return "Invalid task"

            return result

        except Exception as e:
            raise Exception(f"Failed to process query: {str(e)}")

    def upload(self, file_path: str, session_id: str) -> None:
        """
        Upload a PDF file to the service. Creates new session state.
        """
        try:
            pages = load_pdf(file_path)
            docs = chunk_docs(pages)

            # Save only the document content and metadata
            serializable_pages = [
                {"content": page.page_content, "metadata": page.metadata}
                for page in pages
            ]

            # Prepare full text for summarization
            full_text = "\n".join([page.page_content for page in pages])

            # Create state object with proper typing
            state: SessionState = {
                "pages": serializable_pages,
                "full_text": full_text,
                "docs": [
                    {"content": doc.page_content, "metadata": doc.metadata}
                    for doc in docs
                ],
            }

            self.session_state_db.put(session_id, state)

        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}")
