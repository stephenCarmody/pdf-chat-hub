import logging

# Add this at the top of app.py, before any other imports
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Ensure FastAPI's logging is also at DEBUG level
logging.getLogger("fastapi").setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.router import router

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()


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


app = create_app()
app.include_router(router)
