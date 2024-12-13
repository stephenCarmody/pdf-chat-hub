from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


class AppInfo(BaseModel):
    name: str
    version: str
    description: str
