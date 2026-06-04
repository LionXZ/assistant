# src/api/routes.py
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from src.api.schemas import ChatRequest, ChatResponse, HealthResponse
from src.agent.assistant import assistant
from src.config.settings import settings, PROJECT_ROOT
from src.tools.registry import tool_registry
from src.rag.retriever import rag_retriever

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
                import json
                yield f"data: {json.dumps(chunk)}\n\n"
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
    from src.models.chat_model import get_mini_model

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
async def upload_documents(files: list[UploadFile] = File(...)):
    """上传文档 → AI 分类 → 存到对应目录 → 增量索引"""
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
async def delete_document(filepath: str):
    """删除知识库中的文档（支持子目录路径，如 'Python编程/guide.md'）"""
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
