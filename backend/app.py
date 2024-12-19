import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI()

    # Get the API Gateway URL from the environment variable
    api_gateway_url = os.getenv(
        "API_GATEWAY_URL", "li6a6mcfp4.execute-api.eu-west-1.amazonaws.com"
    )

    allowed_origins = [
        "http://localhost:5173",  # Local development
        "https://www.pdfchathub.com",  # Production custom domain
        f"https://{api_gateway_url}",  # API Gateway domain
        "https://li6a6mcfp4.execute-api.eu-west-1.amazonaws.com",  # Hardcoded API Gateway domain
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    return app
