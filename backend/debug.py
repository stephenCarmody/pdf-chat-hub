import uvicorn
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()

if __name__ == "__main__":
    load_dotenv()
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
