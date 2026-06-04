# src/memory/checkpointer.py
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
from src.config.settings import settings


def get_checkpointer():
    """获取 Checkpointer"""
    if settings.DEBUG:
        # 开发环境：内存（重启丢失）
        return MemorySaver()
    else:
        # 生产环境：SQLite 持久化
        return SqliteSaver.from_conn_string(settings.SQLITE_DB_PATH)


# 使用示例
# checkpointer = get_checkpointer()
# config = {"configurable": {"thread_id": "user-001"}}
