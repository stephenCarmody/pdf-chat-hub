import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from dependencies.services import get_pdf_service
from models.api_models import AppInfo, QueryRequest
from services.pdf_chat_service import PDFChatService

UPLOAD_DIR = Path("/tmp/pdf_chat_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/prod")


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
    try:
        result = pdf_service.query(
            query=request.query,
            session_id=request.session_id,
            chat_history=request.chat_history,
        )
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_file(
    pdf_service: Annotated[PDFChatService, Depends(get_pdf_service)],
    file: UploadFile = File(...),
    session_id: str = None,
):
    try:
        file_path = UPLOAD_DIR / file.filename
        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

        pdf_service.upload(str(file_path), session_id)
        return {"message": "File uploaded successfully!", "filename": file.filename}

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process PDF: {str(e)}"
        )
