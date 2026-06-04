# src/app.py
import uvicorn
from src.api.server import app
from src.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.api.server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
