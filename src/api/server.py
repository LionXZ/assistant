# src/api/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.api.routes import router
from src.agent.assistant import assistant
from src.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期事件"""
    # 启动时
    print(f"\n{'='*50}")
    print(f"  {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"  API: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"  Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"{'='*50}\n")

    await assistant.initialize()

    yield

    # 关闭时
    print("\n  shutting down...\n")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI 编程助手 Agent - 基于 LangChain v1.3",
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router, prefix="/api/v1")

    return app


app = create_app()
