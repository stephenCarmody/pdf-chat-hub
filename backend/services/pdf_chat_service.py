import logging
import uuid

from langchain.schema import Document
from langchain_community.chat_message_histories import PostgresChatMessageHistory

from brain.document_processing import DocumentProcessor
from brain.model_router import create_router
from brain.rag import RAGChain
from brain.summariser import SummaryChain
from repositories.session_db import DocumentStore
from repositories.vector_db import VectorStore
from settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PDFChatService:
    def __init__(
        self,
        document_processor: DocumentProcessor,
        vector_store: VectorStore,
        document_store: DocumentStore,
        rag_chain: RAGChain,
        summary_chain: SummaryChain,
    ):
        logger.info("Initializing PDFChatService")
        self.document_processor = document_processor
        self.rag_chain = rag_chain
        self.summary_chain = summary_chain
        self.vector_store = vector_store
        self.document_store = document_store
        self.router = create_router()

    def query(
        self,
        session_id: str,
        doc_id: str,
        question: str,
    ):
        """
        Query the document with a question/task.
        """
        logger.info(
            f"Querying with question: {question}, session_id: {session_id}, doc_id: {doc_id}"
        )

        # Get document content
        full_text = self.document_store.get_document(doc_id)
        if not full_text:
            return "Please upload a document first."

        state_key = f"{session_id}:{doc_id}"
        history = PostgresChatMessageHistory(
            connection_string=settings.connection_string,
            session_id=state_key,
        )

        try:
            result = self.router.invoke(question)

            if result.task.lower() == "q_and_a":
                retriever = self.vector_store.get_retriever(session_id, doc_id)
                result = self.rag_chain.run(question, retriever, history.messages)
            elif result.task.lower() == "summary":
                full_text_doc = [Document(page_content=full_text, metadata={})]
                result = self.summary_chain.run(full_text_doc)
            else:
                return "Invalid task"

            # Add messages to history
            history.add_user_message(question)
            history.add_ai_message(result)

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
            pages = self.document_processor.load_pdf(file_path)
            logger.info(f"Successfully loaded PDF with {len(pages)} pages")

            docs = self.document_processor.chunk_docs(pages)
            doc_id = str(uuid.uuid4())

            # Prepare and store full text for summarization
            full_text = "\n".join([page.page_content for page in pages])
            self.document_store.put_document(
                doc_id=doc_id,
                session_id=session_id,
                full_text=full_text,
                filename=file_path,
            )
            logger.info("Successfully saved document content")

            # Add documents to vector store with session and doc identifiers
            self.vector_store.add_documents(docs, session_id, doc_id)
            logger.info("Successfully added documents to vector store")

            return {"doc_id": doc_id, "message": "File uploaded successfully!"}

        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to process PDF: {str(e)}")
