from io import BytesIO

from langchain.schema import Document

from brain.document_processing import chunk_docs, load_pdf
from brain.model_router import create_router
from brain.rag import create_rag_chain
from brain.summariser import create_summary_chain
from brain.vector_db import create_db, create_retriever

import os
import boto3
import pickle
from botocore.exceptions import ClientError

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PDFChatService:
    def __init__(self):
        logger.info("Initializing PDFChatService")
        self.bucket_name = os.getenv("SESSION_STATE_BUCKET")
        self.s3_client = boto3.client("s3")
        self.router = create_router()

    def query(self, query: str, session_id: str):
        """
        Query the document with a question / task.
        """
        # Load state for this session
        state = self._load_session_state(session_id)
        if not state:
            return "Please upload a document first."

        try:
            # Recreate documents from stored state
            docs = [Document(
                page_content=doc['content'],
                metadata=doc['metadata']
            ) for doc in state['docs']]

            # Recreate chains for each query
            db = create_db(docs)
            retriever = create_retriever(db)
            rag_chain = create_rag_chain(retriever)
            summary_chain = create_summary_chain()

            # Route the query
            result = self.router.invoke(query)

            if result.task.lower() == "q_and_a":
                result = rag_chain.invoke(query)
            elif result.task.lower() == "summary":
                full_text_doc = [Document(page_content=state['full_text'], metadata={})]
                result = summary_chain.invoke({"context": full_text_doc})
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

            # Create vector DB and save the documents
            db = create_db(docs)
            
            # Save only the document content and metadata
            serializable_pages = [{
                'content': page.page_content,
                'metadata': page.metadata
            } for page in pages]

            # Prepare full text for summarization
            full_text = "\n".join([page.page_content for page in pages])
            
            # Save state with only serializable data
            self._save_session_state(session_id, {
                'pages': serializable_pages,
                'full_text': full_text,
                'docs': [{
                    'content': doc.page_content,
                    'metadata': doc.metadata
                } for doc in docs]
            })

        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}")

    def _save_session_state(self, session_id: str, state):
        """Save current state to S3."""
        try:
            serialized_state = pickle.dumps(state)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self._get_session_state_key(session_id),
                Body=serialized_state
            )
        except Exception as e:
            raise Exception(f"Failed to save state to S3: {str(e)}")

    def _load_session_state(self, session_id: str):
        """Load state from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self._get_session_state_key(session_id)
            )
            return pickle.loads(response['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise Exception(f"Failed to load state from S3: {str(e)}")

    def _get_session_state_key(self, session_id: str) -> str:
        """Generate S3 key for the session state."""
        return f"chat_states/{session_id}/state.pkl"
