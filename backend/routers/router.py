import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from dependencies.services import get_pdf_service
from models.api_models import AppInfo, QueryRequest
from services.pdf_chat_service import PDFChatService

logger = logging.getLogger(__name__)

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
    logger.info(f"Querying for session {request.session_id}")
    logger.info(f"Query: {request.query}")
    logger.info(f"Doc ID: {request.doc_id}")

    try:
        result = pdf_service.query(
            session_id=request.session_id,
            doc_id=request.doc_id,
            question=request.query,
        )
        return {"message": result}
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_file(
    pdf_service: Annotated[PDFChatService, Depends(get_pdf_service)],
    file: UploadFile = File(...),
    session_id: str = Form(...),
):
    logger.info(f"Uploading file for session {session_id}")
    try:
        file_path = UPLOAD_DIR / file.filename
        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

        result = pdf_service.upload(str(file_path), session_id)
        return {
            "doc_id": result["doc_id"],
            "message": result["message"],
            "filename": file.filename,
        }

    except Exception as e:
        logger.exception("Upload failed with error:")
        raise HTTPException(status_code=500, detail=str(e))
