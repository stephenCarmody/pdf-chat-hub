from mangum import Mangum
import logging
import boto3
import json
import os

from app import create_app
from routers.router import router

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients outside the handler
secrets_client = boto3.client('secretsmanager')

# Get the secret during cold start
try:
    secret_name = os.environ['OPENAI_SECRET_NAME']
    response = secrets_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    os.environ['OPENAI_API_KEY'] = secret['OPENAI_API_KEY']
    logger.info("Successfully loaded OpenAI API key during initialization")
except Exception as e:
    logger.error(f"Error loading secret during initialization: {str(e)}")
    raise

# Create FastAPI app and include router
app = create_app()
app.include_router(router)

# Create Mangum handler
handler = Mangum(app)
