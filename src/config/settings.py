# src/config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()


class Settings:
    """全局配置"""

    # ===== 项目 =====
    PROJECT_NAME: str = "DevAssistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ===== 大模型 (DeepSeek, OpenAI 兼容) =====
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_MODEL_MINI: str = os.getenv("LLM_MODEL_MINI", "deepseek-chat")

    # ===== Embedding 模型 =====
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # ===== 搜索 API =====
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # ===== 向量数据库 =====
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "data" / "chroma"))

    # ===== SQLite Checkpointer =====
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", str(PROJECT_ROOT / "data" / "checkpoints.db"))

    # ===== LangSmith =====
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "dev-assistant")
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

    # ===== Agent =====
    MAX_MODEL_RETRIES: int = int(os.getenv("MAX_MODEL_RETRIES", "3"))
    MAX_TOOL_RETRIES: int = int(os.getenv("MAX_TOOL_RETRIES", "2"))
    SUMMARIZATION_TRIGGER_FRACTION: float = float(os.getenv("SUMMARIZATION_TRIGGER_FRACTION", "0.8"))

    # ===== API =====
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))


# 单例
settings = Settings()
