from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(
        description="The role of the message sender, either 'user' or 'assistant'"
    )
    content: str = Field(description="The content of the message")


class QueryRequest(BaseModel):
    query: str
    session_id: str
    doc_id: str
    chat_history: Optional[List[ChatMessage]] = None


class AppInfo(BaseModel):
    name: str
    version: str
    description: str
