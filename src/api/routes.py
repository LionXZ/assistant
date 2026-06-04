# src/api/routes.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.api.schemas import ChatRequest, ChatResponse, HealthResponse
from src.agent.assistant import assistant
from src.config.settings import settings
from src.tools.registry import tool_registry

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        tools_count=len(tool_registry.get_all_tools()),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """同步对话"""
    try:
        result = await assistant.chat(
            message=request.message,
            thread_id=request.thread_id,
            user_id=request.user_id,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式对话"""
    async def generate():
        try:
            async for chunk in assistant.chat_stream(
                message=request.message,
                thread_id=request.thread_id,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
