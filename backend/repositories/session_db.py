import json
import logging
import os
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DocumentState(TypedDict):
    content: str
    metadata: Dict[str, any]


class SessionState(TypedDict):
    pages: List[Dict[str, Any]]
    full_text: str
    docs: List[Dict[str, Any]]
    chat_history: List[Tuple[str, str]]  # List of (query, response) pairs


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


# TODO: Figure out where folder is on system -> Implement some cleanup for tests
class FileSystemSessionStateDB(SessionStateDB):
    def __init__(self, storage_dir: str = "/tmp/pdf_chat_sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using file system session state database at {self.storage_dir}")

    def put(self, session_id: str, state: SessionState) -> None:
        file_path = self.storage_dir / f"{session_id}.json"
        logger.info(f"Saving state to {file_path}")
        with open(file_path, "w") as f:
            json.dump(state, f)
        logger.info(f"Successfully saved state for session {session_id}")

    def get(self, session_id: str) -> Optional[SessionState]:
        file_path = self.storage_dir / f"{session_id}.json"
        logger.info(f"Trying to load state from {file_path}")
        if not file_path.exists():
            logger.warning(f"No state file found for session {session_id}")
            return None
        with open(file_path, "r") as f:
            state = json.load(f)
            logger.info(f"Loaded state.")
            return state
