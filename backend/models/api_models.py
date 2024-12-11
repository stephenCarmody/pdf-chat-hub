from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class AppInfo(BaseModel):
    name: str
    version: str
    description: str
