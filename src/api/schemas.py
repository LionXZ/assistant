# src/api/schemas.py
from pydantic import BaseModel, Field
from typing import Optional


# ---- 认证 ----
class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=30)
    email: str
    password: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class UserResponse(BaseModel):
    id: int
    username: str
    email: str


# ---- 对话 ----
class ChatRequest(BaseModel):
    message: str = Field(description="用户消息")
    thread_id: str = Field(default="default", description="会话 ID")


class ChatResponse(BaseModel):
    content: str = Field(description="回复内容")
    thread_id: str = Field(description="会话 ID")
    message_count: int = Field(description="当前会话消息数")


class HealthResponse(BaseModel):
    status: str
    version: str
    tools_count: int


# ---- 会话 ----
class SessionItem(BaseModel):
    thread_id: str
    title: str
    updated_at: str


class SessionListResponse(BaseModel):
    sessions: list[SessionItem]
