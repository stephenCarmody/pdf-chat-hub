import json
import logging
import os
import traceback
import sys

import boto3
from mangum import Mangum
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app import app
from routers.router import router

# Configure logging with more detail
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Add error handling middleware to FastAPI app
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

# Initialize AWS clients outside the handler
secrets_client = boto3.client("secretsmanager")

# Get the secret during cold start
try:
    secret_name = os.environ["OPENAI_SECRET_NAME"]
    logger.info(f"Loading secret: {secret_name}")
    response = secrets_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    os.environ["OPENAI_API_KEY"] = secret["OPENAI_API_KEY"]
    logger.info("Successfully loaded OpenAI API key")
except Exception as e:
    logger.error(f"Secret loading failed: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

# Create Mangum handler with debug mode
handler = Mangum(app, lifespan="off")

logger.info("Lambda handler initialized successfully")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
