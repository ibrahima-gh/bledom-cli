import logging
import uvicorn
from bledom.api import app  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)

if __name__ == "__main__":
    uvicorn.run(
        "bledom.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
