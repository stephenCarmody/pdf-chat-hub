import logging
import uuid
from typing import List, Optional, Tuple

from langchain.schema import Document

from brain.document_processing import chunk_docs, load_pdf
from brain.model_router import create_router
from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import SessionState, SessionStateDB
from repositories.vector_db import VectorStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PDFChatService:
    def __init__(
        self,
        vector_store: VectorStore,
        session_state_db: SessionStateDB,
        rag_chain: RAGChain,
        summary_chain: SummaryChain,
    ):
        logger.info("Initializing PDFChatService")
        self.rag_chain = rag_chain
        self.summary_chain = summary_chain
        self.vector_store = vector_store
        self.session_state_db = session_state_db
        self.router = create_router()

    def query(
        self,
        query: str,
        session_id: str,
        doc_id: str,
        chat_history: Optional[List[Tuple[str, str]]] = None,
    ):
        """
        Query the document with a question/task.
        """
        logger.info(
            f"Querying with query: {query}, session_id: {session_id}, doc_id: {doc_id}"
        )
        state_key = f"{session_id}:{doc_id}"
        state = self.session_state_db.get(state_key)
        if not state:
            return "Please upload a document first."
        current_chat_history = list(chat_history) if chat_history is not None else []

        try:
            result = self.router.invoke(query)

            # TODO: Implement strategy pattern here
            if result.task.lower() == "q_and_a":
                retriever = self.vector_store.get_retriever(session_id, doc_id)
                result = self.rag_chain.run(query, retriever, chat_history or [])
            elif result.task.lower() == "summary":
                full_text_doc = [Document(page_content=state["full_text"], metadata={})]
                result = self.summary_chain.run(full_text_doc)
            else:
                return "Invalid task"

            current_chat_history.append((query, result))
            state["chat_history"] = current_chat_history
            self.session_state_db.put(state_key, state)

            return result

        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}", exc_info=True)
            raise Exception(f"Failed to process query: {str(e)}")

    def upload(self, file_path: str, session_id: str) -> dict:
        """
        Upload a PDF file to the service. Creates new session state.
        Returns document ID and filename.
        """
        logger.info(f"Starting upload process for session_id: {session_id}")

        try:
            pages = load_pdf(file_path)
            logger.info(f"Successfully loaded PDF with {len(pages)} pages")

            docs = chunk_docs(pages)
            doc_id = str(uuid.uuid4())

            # Prepare full text for summarization
            full_text = "\n".join([page.page_content for page in pages])

            # Create state object with proper typing
            state: SessionState = {
                "full_text": full_text,
                "chat_history": [],
            }

            # Store with combined session_id and doc_id as key
            self.session_state_db.put(f"{session_id}:{doc_id}", state)
            logger.info("Successfully saved state to database")

            # Add documents to vector store with session and doc identifiers
            self.vector_store.add_documents(docs, session_id, doc_id)
            logger.info("Successfully added documents to vector store")

            return {"doc_id": doc_id, "message": "File uploaded successfully!"}

        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to process PDF: {str(e)}")
