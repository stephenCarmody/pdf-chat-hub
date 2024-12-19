from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(
        description="The role of the message sender, either 'user' or 'assistant'"
    )
    content: str = Field(description="The content of the message")


class QueryRequest(BaseModel):
    query: str = Field(description="The query to be sent to the PDF chat service")
    session_id: str | None = None
    chat_history: list[Message] = []


class AppInfo(BaseModel):
    name: str
    version: str
    description: str
