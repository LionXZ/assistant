# backend/src/app.py
import sys
from pathlib import Path

# 确保项目根目录在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import uvicorn
from backend.src.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.src.api.server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
