import uvicorn
from bledom.api import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run(
        "bledom.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
