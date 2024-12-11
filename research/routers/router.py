from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi import UploadFile
import uvicorn

class QueryRequest(BaseModel):
    query: str

class UploadRequest(BaseModel):
    file: UploadFile

class AppInfo(BaseModel):
    name: str
    version: str
    description: str

app = FastAPI()

from services.pdf_chat_service import PDFChatService


def get_chat_service():
    return PDFChatService()

@app.get("/")
def read_root():
    return AppInfo(name="Chat with PDFs", version="0.1.0", description="A simple chatbot that can answer questions about a PDF file.")

@app.post("/query")
def query(request: QueryRequest, chat_service = Depends(get_chat_service)):
    response = chat_service.query(request.query)
    return {"message": response}

@app.post("/upload")
async def upload(file: UploadFile):
    try:
        # Read the file contents as bytes
        contents = await file.read()
        return {"message": "File uploaded successfully!", "filename": file.filename}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)