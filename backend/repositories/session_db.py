import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

import boto3
import psycopg2
from botocore.exceptions import ClientError
from psycopg2.extras import RealDictCursor

from settings import settings

logger = logging.getLogger(__name__)


class DocumentStore(ABC):
    """Store for document full text content."""

    @abstractmethod
    def put_document(
        self,
        doc_id: str,
        session_id: str,
        full_text: str,
        filename: Optional[str] = None,
    ) -> None:
        """Store document content"""
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[str]:
        """Retrieve document content"""
        pass


class InMemoryDocumentStore(DocumentStore):
    """In-memory implementation of DocumentStore for testing."""

    def __init__(self):
        self._docs: Dict[str, Dict] = {}
        logger.info("Using in-memory document store")

    def put_document(
        self,
        doc_id: str,
        session_id: str,
        full_text: str,
        filename: Optional[str] = None,
    ) -> None:
        self._docs[doc_id] = {
            "session_id": session_id,
            "full_text": full_text,
            "filename": filename,
        }
        logger.info(f"Saved document {doc_id} to memory")

    def get_document(self, doc_id: str) -> Optional[str]:
        doc = self._docs.get(doc_id)
        return doc["full_text"] if doc else None


class PostgresDocumentStore(DocumentStore):
    def __init__(self):
        self.connection_string = settings.connection_string

    def put_document(
        self,
        doc_id: str,
        session_id: str,
        full_text: str,
        filename: Optional[str] = None,
    ) -> None:
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO documents (id, session_id, full_text, filename)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (doc_id, session_id, full_text, filename),
                )

    def get_document(self, doc_id: str) -> Optional[str]:
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT full_text 
                    FROM documents 
                    WHERE id = %s
                    """,
                    (doc_id,),
                )
                result = cur.fetchone()
                return result["full_text"] if result else None


class S3DocumentStore(DocumentStore):
    """S3-based implementation of DocumentStore."""

    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self.s3_client = boto3.client("s3")
        logger.info(f"Using S3 document store with bucket: {settings.s3_bucket_name}")

    def put_document(
        self,
        doc_id: str,
        session_id: str,
        full_text: str,
        filename: Optional[str] = None,
    ) -> None:
        try:
            # Store the document content
            key = self._get_document_key(doc_id)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=full_text.encode("utf-8"),
                Metadata={"session_id": session_id, "filename": filename or ""},
            )
            logger.info(f"Successfully stored document {doc_id} in S3")
        except Exception as e:
            logger.error(f"Failed to store document in S3: {str(e)}")
            raise

    def get_document(self, doc_id: str) -> Optional[str]:
        try:
            key = self._get_document_key(doc_id)
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve document from S3: {str(e)}")
            raise

    def _get_document_key(self, doc_id: str) -> str:
        """Generate S3 key for a document."""
        return f"documents/{doc_id}/content.txt"
