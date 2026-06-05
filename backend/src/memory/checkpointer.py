# src/memory/checkpointer.py
from backend.src.config.settings import settings
from backend.src.memory.mysql_saver import MySQLSaver


def get_checkpointer():
    """
    获取 MySQL Checkpointer — 对话状态持久化到 dev-assistant 库。
    """
    return MySQLSaver.from_config(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset=settings.DB_CHARSET,
    )
