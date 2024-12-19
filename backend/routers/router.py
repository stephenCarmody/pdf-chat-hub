import sys
import traceback
import uuid
from pathlib import Path
from typing import Annotated, List, Tuple

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from dependencies.services import get_pdf_service
from models.api_models import AppInfo, QueryRequest
from services.pdf_chat_service import PDFChatService

UPLOAD_DIR = Path("/tmp/pdf_chat_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/prod")


class ChatMessage(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    query: str
    session_id: str
    chat_history: List[Tuple[str, str]] = []


@router.get("/")
def read_root():
    return AppInfo(
        name="Chat with PDFs",
        version="0.1.0",
        description="A simple chatbot that can answer questions about a PDF file.",
    )


@router.get("/session")
def get_session():
    return {"session": str(uuid.uuid4())}


@router.post("/query")
async def query(
    request: QueryRequest,
    pdf_service: Annotated[PDFChatService, Depends(get_pdf_service)],
):
    result = pdf_service.query(
        query=request.query,
        session_id=request.session_id,
        chat_history=request.chat_history,
    )
    return {"message": result}


@router.post("/upload")
async def upload_file(
    pdf_service: Annotated[PDFChatService, Depends(get_pdf_service)],
    file: UploadFile = File(...),
    session_id: str = None,
):
    try:
        print(
            f"Starting file upload... Python version: {sys.version}. Session ID: {session_id}"
        )
        print(f"Upload directory: {UPLOAD_DIR}")
        print(f"File name: {file.filename}")

        file_path = UPLOAD_DIR / file.filename
        contents = await file.read()
        print(f"File contents read, size: {len(contents)} bytes")

        try:
            with open(file_path, "wb") as f:
                f.write(contents)
            print(f"File written to {file_path}")

            print("Starting PDF processing...")
            pdf_service.upload(str(file_path), session_id)
            print("PDF processing completed successfully")

            return {"message": "File uploaded successfully!", "filename": file.filename}

        except Exception as e:
            error_msg = f"PDF processing error: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        error_msg = f"File upload error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
