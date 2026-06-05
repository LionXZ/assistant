# src/api/routes.py
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from backend.src.api.schemas import (
    ChatRequest, ChatResponse, HealthResponse,
    RegisterRequest, LoginRequest, AuthResponse, UserResponse,
    SessionItem, SessionListResponse,
)
from backend.src.agent.assistant import assistant
from backend.src.config.settings import settings, PROJECT_ROOT
from backend.src.tools.registry import tool_registry
from backend.src.rag.retriever import rag_retriever
from backend.src.auth.auth import get_current_user, create_token
from backend.src.auth.email import send_verification_code
from backend.src.auth.models import create_user, verify_user, get_user_by_id
from backend.src.auth.models import list_user_sessions, upsert_session, delete_session
from backend.src.auth.models import save_message, get_session_messages
from backend.src.auth.models import verify_email, is_admin_user
from backend.src.auth.models import set_reset_token, reset_password

router = APIRouter()


# ===== AI 智能标题 =====

async def _auto_title(user_id: int, thread_id: str, user_msg: str, ai_reply: str = ""):
    """用 AI 生成会话标题 (2-10字)，优先用用户消息"""
    try:
        from backend.src.models.chat_model import get_mini_model
        model = get_mini_model(temperature=0.3)
        text = ai_reply if ai_reply else user_msg
        prompt = f"用2-10个汉字为以下内容起一个简短标题，不要标点符号：\n\n{text[:200]}\n\n标题："
        result = await model.ainvoke(prompt)
        title = result.content.strip().replace("'", "").replace('"', "").replace("标题：", "").replace(" ", "")
        if len(title) > 20:
            title = title[:20]
        if title:
            upsert_session(user_id, thread_id, title)
    except Exception:
        pass


# ===== 认证 =====

@router.post("/auth/register")
async def register(req: RegisterRequest):
    user = create_user(req.username, req.email, req.password)
    if not user:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在，admin 为系统保留账户")

    # 发送验证码
    success = send_verification_code(user["email"], user["verification_code"])
    if not success:
        raise HTTPException(status_code=500, detail="验证码发送失败，请检查邮箱配置")

    return {"user_id": user["id"], "message": "验证码已发送，请查收邮箱"}


@router.post("/auth/send-code")
async def resend_code(user_id: int):
    """重发验证码 (注册后使用)"""
    from backend.src.auth.models import get_user_verification_code
    info = get_user_verification_code(user_id)
    if not info:
        raise HTTPException(status_code=404, detail="用户不存在")
    success = send_verification_code(info["email"], info["verification_code"])
    if not success:
        raise HTTPException(status_code=500, detail="发送失败")
    return {"message": "验证码已重新发送"}


@router.post("/auth/verify-email")
async def verify_user_email(user_id: int, code: str):
    """验证邮箱 (注册后使用，不需要登录)"""
    if verify_email(user_id, code):
        return {"message": "邮箱验证成功，请登录"}
    raise HTTPException(status_code=400, detail="验证码错误")


@router.post("/auth/forgot-password")
async def forgot_password(email: str):
    """忘记密码 — 发送重置验证码"""
    result = set_reset_token(email)
    if not result:
        raise HTTPException(status_code=404, detail="该邮箱未注册")
    success = send_verification_code(result["email"], result["reset_token"])
    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")
    return {"message": "重置验证码已发送到您的邮箱"}


@router.post("/auth/reset-password")
async def do_reset_password(email: str, code: str, new_password: str):
    """重置密码"""
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")
    if reset_password(email, code, new_password):
        return {"message": "密码重置成功，请登录"}
    raise HTTPException(status_code=400, detail="验证码错误")


@router.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    user = verify_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误，或邮箱未验证")
    token = create_token(user["id"], user["username"])
    return {"token": token, "user": {"id": user["id"], "username": user["username"], "email": user["email"], "is_admin": bool(user.get("is_admin"))}}


@router.get("/auth/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(current_user["id"])
    return {"id": user["id"], "username": user["username"], "email": user["email"], "is_admin": bool(user.get("is_admin"))}


# ===== 会话管理 =====

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(current_user: dict = Depends(get_current_user)):
    sessions = list_user_sessions(current_user["id"])
    return {"sessions": [
        {"thread_id": s["thread_id"], "title": s["title"], "updated_at": str(s["updated_at"])}
        for s in sessions
    ]}


@router.delete("/sessions/{thread_id}")
async def delete_user_session(thread_id: str, current_user: dict = Depends(get_current_user)):
    delete_session(current_user["id"], thread_id)
    return {"deleted": thread_id}


@router.get("/sessions/{thread_id}/messages")
async def get_thread_messages(thread_id: str, current_user: dict = Depends(get_current_user)):
    """获取会话历史消息"""
    msgs = get_session_messages(current_user["id"], thread_id)
    return {"messages": msgs}


# ===== 健康检查 =====

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        tools_count=len(tool_registry.get_all_tools()),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """同步对话"""
    try:
        sessions = list_user_sessions(current_user["id"])
        is_new = not any(s["thread_id"] == request.thread_id for s in sessions)

        upsert_session(current_user["id"], request.thread_id, request.message[:30])

        if is_new:
            await _auto_title(current_user["id"], request.thread_id, request.message)

        result = await assistant.chat(
            message=request.message,
            thread_id=request.thread_id,
            user_id=str(current_user["id"]),
        )

        save_message(current_user["id"], request.thread_id, "user", request.message)
        if result.get("content"):
            save_message(current_user["id"], request.thread_id, "assistant", result["content"])

        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """流式对话"""
    sessions = list_user_sessions(current_user["id"])
    is_new = not any(s["thread_id"] == request.thread_id for s in sessions)

    # 先用首条消息做临时标题
    upsert_session(current_user["id"], request.thread_id, request.message[:30])

    # 新会话：同步生成 AI 标题（不等回复，直接用问题生成）
    if is_new:
        await _auto_title(current_user["id"], request.thread_id, request.message)

    ai_reply_parts = []

    async def generate():
        nonlocal ai_reply_parts
        try:
            async for chunk in assistant.chat_stream(
                message=request.message,
                thread_id=request.thread_id,
                user_id=str(current_user["id"]),
            ):
                import json
                if not chunk.startswith('🔧') and not chunk.startswith('\n📋'):
                    ai_reply_parts.append(chunk)
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            save_message(current_user["id"], request.thread_id, "user", request.message)
            ai_text = ''.join(ai_reply_parts).strip()
            if ai_text:
                save_message(current_user["id"], request.thread_id, "assistant", ai_text)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ===== RAG 文档管理 =====

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


def _read_text_content(filepath: str, max_chars: int = 800) -> str:
    """读取文件前 N 个字符的文本内容"""
    path = Path(filepath)
    if path.suffix.lower() == ".pdf":
        return f"[PDF文档] {path.name}"

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_chars)
    except Exception:
        return f"[文件] {path.name}"


async def _classify_document(filename: str, content: str) -> str:
    """用 AI 识别文档主题，返回分类目录名（如 'Python编程'、'数据库'）"""
    from backend.src.models.chat_model import get_mini_model

    model = get_mini_model(temperature=0.1)

    prompt = f"""你是一个文档分类助手。根据以下文档的文件名和内容片段，给它分一个最合适的类别目录名。

要求：
- 只用中文，2-6个字
- 例如：'Python编程'、'Go语言'、'数据库'、'前端开发'、'运维部署'、'AI与机器学习'、'系统设计'、'安全'、'通用技术'
- 如果无法判断，返回 '通用技术'

文件名：{filename}
内容片段：
{content[:500]}

类别目录名："""

    try:
        result = await model.ainvoke(prompt)
        category = result.content.strip()
        # 清理 - 去掉可能的引号和多余空格
        category = category.replace("'", "").replace('"', "").replace("、", "-").strip()
        if len(category) > 20:
            category = category[:20]
        if not category:
            category = "通用技术"
        print(f"  🤖 AI 分类: '{filename}' → '{category}'")
        return category
    except Exception as e:
        print(f"  ⚠ AI 分类失败: {e}, 使用默认分类")
        return "通用技术"


@router.get("/rag/documents")
async def list_documents():
    """列出知识库中的文档（含子目录）"""
    docs_dir = PROJECT_ROOT / "data" / "documents"
    if not docs_dir.exists():
        return {"documents": [], "indexed_count": 0}

    files = []
    for f in sorted(docs_dir.rglob("*")):
        if f.is_file() and f.suffix in ALLOWED_EXTENSIONS:
            files.append(str(f.relative_to(docs_dir)))

    count = 0
    if rag_retriever.vector_store:
        try:
            count = rag_retriever.vector_store._collection.count()
        except Exception:
            pass

    return {"documents": files, "indexed_count": count}


@router.post("/rag/upload")
async def upload_documents(files: list[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    """上传文档 → AI 分类 → 存到对应目录 → 增量索引 (仅 admin)"""
    if not is_admin_user(current_user["id"]):
        raise HTTPException(status_code=403, detail="仅管理员可上传文档")
    docs_dir = PROJECT_ROOT / "data" / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    uploaded = 0
    failed = 0
    total_chunks = 0
    errors = []

    for file in files:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            failed += 1
            errors.append(f"{file.filename}: 不支持的类型 {suffix}")
            continue

        safe_name = Path(file.filename).name
        content_bytes = await file.read()

        # 1. 先存到临时位置，提取文本内容用于 AI 分类
        tmp_path = docs_dir / safe_name
        with open(tmp_path, "wb") as f:
            f.write(content_bytes)

        text_preview = _read_text_content(str(tmp_path))

        # 2. AI 分类 → 创建目录 → 移动文件
        category = await _classify_document(safe_name, text_preview)
        category_dir = docs_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        dest = category_dir / safe_name
        # 如果已有同名文件就不移动（保留在临时位置）
        if dest.exists():
            tmp_path.unlink()  # 删临时文件
            failed += 1
            errors.append(f"{safe_name}: 已存在同名文件")
            continue

        tmp_path.rename(dest)
        print(f"  📁 {safe_name} → {category}/")

        # 3. 增量索引
        try:
            chunks = rag_retriever.add_file(str(dest))
            total_chunks += chunks
            uploaded += 1
        except Exception as e:
            failed += 1
            errors.append(f"{safe_name}: 索引失败 - {e}")

    return {
        "uploaded": uploaded,
        "failed": failed,
        "total_chunks": total_chunks,
        "errors": errors,
    }


@router.post("/rag/delete")
async def delete_document(filepath: str, current_user: dict = Depends(get_current_user)):
    """删除知识库中的文档 (仅 admin)"""
    if not is_admin_user(current_user["id"]):
        raise HTTPException(status_code=403, detail="仅管理员可删除文档")
    docs_dir = PROJECT_ROOT / "data" / "documents"
    # 防路径穿越
    safe_path = Path(filepath).as_posix().lstrip("/")
    fullpath = docs_dir / safe_path

    if not fullpath.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(fullpath.resolve()).startswith(str(docs_dir.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")

    fullpath.unlink()

    # 如果目录为空则删除
    parent = fullpath.parent
    if parent != docs_dir and not any(parent.iterdir()):
        parent.rmdir()

    return {"deleted": filepath, "message": "已删除"}
