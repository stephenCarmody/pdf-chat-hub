from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class Message(BaseModel):
    role: str = Field(
        description="The role of the message sender, either 'user' or 'assistant'"
    )
    content: str = Field(description="The content of the message")


class QueryRequest(BaseModel):
    query: str
    session_id: str
    doc_id: str
    chat_history: Optional[List[Dict[str, str]]] = None


class AppInfo(BaseModel):
    name: str
    version: str
    description: str
