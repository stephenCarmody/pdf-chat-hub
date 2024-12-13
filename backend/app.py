from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Local development
            f"https://{os.getenv('CLOUDFRONT_DOMAIN')}"  # Production
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app
