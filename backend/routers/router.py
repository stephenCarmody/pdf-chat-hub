from pathlib import Path
import sys
import traceback

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Annotated

from models.api_models import AppInfo, QueryRequest
from services.pdf_chat_service import PDFChatService
from dependencies.services import get_pdf_service

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

@router.post("/query")
async def query(
    request: QueryRequest,
    pdf_service: Annotated[PDFChatService, Depends(get_pdf_service)]
):
    result = pdf_service.query(request.query)
    return {"message": result}

@router.post("/upload")
async def upload_file(
    pdf_service: Annotated[PDFChatService, Depends(get_pdf_service)],
    file: UploadFile = File(...)
):
    try:
        print(f"Starting file upload... Python version: {sys.version}")
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
            pdf_service.upload(str(file_path))
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
