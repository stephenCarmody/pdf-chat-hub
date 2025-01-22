from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: str
    doc_id: str


class AppInfo(BaseModel):
    name: str
    version: str
    description: str
