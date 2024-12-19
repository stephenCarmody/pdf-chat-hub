import logging
import os
import pickle
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, TypedDict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DocumentState(TypedDict):
    content: str
    metadata: Dict[str, any]


class SessionState(TypedDict):
    pages: List[DocumentState]
    full_text: str
    docs: List[DocumentState]


class SessionStateDB(ABC):
    @abstractmethod
    def put(self, session_id: str, state: SessionState) -> None:
        """Store state for a session"""
        pass

    @abstractmethod
    def get(self, session_id: str) -> Optional[SessionState]:
        """Retrieve state for a session"""
        pass


class InMemorySessionStateDB(SessionStateDB):
    def __init__(self):
        self._db: Dict[str, SessionState] = {}
        logger.info("Using in-memory session state database")

    def put(self, session_id: str, state: SessionState) -> None:
        self._db[session_id] = state
        logger.info(f"Saved state for session {session_id}")

    def get(self, session_id: str) -> Optional[SessionState]:
        return self._db.get(session_id)


class S3SessionStateDB(SessionStateDB):
    def __init__(self):
        self.bucket_name = os.getenv("SESSION_STATE_BUCKET")
        self.s3_client = boto3.client("s3")

    def put(self, session_id: str, state: SessionState) -> None:
        serialized_state = pickle.dumps(state)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self._get_key(session_id),
            Body=serialized_state,
        )

    def get(self, session_id: str) -> Optional[SessionState]:
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=self._get_key(session_id)
            )
            return pickle.loads(response["Body"].read())
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

    def _get_key(self, session_id: str) -> str:
        return f"chat_states/{session_id}/state.pkl"
