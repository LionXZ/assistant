# src/rag/embedder.py
import os
from src.config.settings import settings

# 关键: 禁止 HuggingFace 联网检查更新 (国内网络不通)
os.environ["HF_HUB_OFFLINE"] = "1"


def get_embeddings():
    """
    获取嵌入模型。

    优先用 OpenAI (填 OPENAI_API_KEY), 没填则自动用本地小模型 (~100MB)。
    """
    if settings.OPENAI_API_KEY:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    # 本地小模型: BAAI/bge-small-zh-v1.5 (~100MB, 已缓存在 ~/.cache/huggingface/)
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs={"device": "cpu", "local_files_only": True},
        encode_kwargs={"normalize_embeddings": True},
    )
