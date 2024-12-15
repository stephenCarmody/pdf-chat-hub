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
    def __init__(self, session_id: str):
        logger.info(f"Initializing PDFChatService with session_id: {session_id}")

        self.session_id = session_id
        self.bucket_name = os.getenv("SESSION_STATE_BUCKET")
        self.s3_client = boto3.client("s3")

        loaded_state = self._load_session_state()
        if loaded_state:
            logger.info(f"Loaded state from S3 for session_id: {session_id}")
        else:
            logger.info(f"No state found for session_id: {session_id}. Creating new state!")
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

        self._save_session_state()
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

            self._save_session_state()
        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}")

    def _save_session_state(self):
        """Save current state to S3."""
        # Only save the text content and metadata, not the full objects
        state = {
            'pages_content': [{'page_content': page.page_content, 'metadata': page.metadata} for page in self.pages] if self.pages else None,
            'full_text': self.full_text_doc[0].page_content if self.full_text_doc else None
        }
        
        try:
            serialized_state = pickle.dumps(state)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self._get_session_state_key(),
                Body=serialized_state
            )
        except Exception as e:
            raise Exception(f"Failed to save state to S3: {str(e)}")

    def _load_session_state(self):
        """Load state from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self._get_session_state_key()
            )
            serialized_state = response['Body'].read()
            state = pickle.loads(serialized_state)
            
            if state:
                # Reconstruct the Document objects
                self.pages = [Document(page_content=p['page_content'], metadata=p['metadata']) 
                             for p in state['pages_content']] if state['pages_content'] else None
                self.full_text_doc = [Document(page_content=state['full_text'], metadata={})] if state['full_text'] else None
                
                # Recreate the chains
                if self.pages:
                    docs = chunk_docs(self.pages)
                    db = create_db(docs)
                    retriever = create_retriever(db)
                    self.rag_chain = create_rag_chain(retriever)
                    self.summary_chain = create_summary_chain()
                    self.router = create_router()
                return state  # Return the state instead of True
            return None
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise Exception(f"Failed to load state from S3: {str(e)}")

    def _get_session_state_key(self) -> str:
        """Generate S3 key for the session state."""
        return f"chat_states/{self.session_id}/state.pkl"
