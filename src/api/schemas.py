# src/api/schemas.py
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(description="用户消息")
    thread_id: str = Field(default="default", description="会话 ID（用于多轮对话）")
    user_id: Optional[str] = Field(default=None, description="用户 ID（用于个性化）")


class ChatResponse(BaseModel):
    """对话响应"""
    content: str = Field(description="回复内容")
    thread_id: str = Field(description="会话 ID")
    message_count: int = Field(description="当前会话消息数")


class HealthResponse(BaseModel):
    """健康检查"""
    status: str
    version: str
    tools_count: int
