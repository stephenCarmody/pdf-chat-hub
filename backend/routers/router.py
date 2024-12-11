import tempfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from models.api_models import AppInfo, QueryRequest
from services.pdf_chat_service import PDFChatService

UPLOAD_DIR = Path(tempfile.gettempdir()) / "pdf_chat_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your Vue dev server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pdf_service = PDFChatService()


@app.get("/")
def read_root():
    return AppInfo(
        name="Chat with PDFs",
        version="0.1.0",
        description="A simple chatbot that can answer questions about a PDF file.",
    )


@app.post("/query")
async def query(request: QueryRequest):
    result = pdf_service.query(request.query)
    return {"message": result}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    file_path = UPLOAD_DIR / file.filename

    contents = await file.read()

    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        pdf_service.upload(str(file_path))
        return {"message": "File uploaded successfully!", "filename": file.filename}
    except Exception as e:
        return {"error": f"Failed to process PDF: {str(e)}"}, 400


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
