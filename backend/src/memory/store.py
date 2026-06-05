# src/memory/store.py
from langgraph.store.memory import InMemoryStore
from typing import Optional, Dict, Any


class UserMemoryStore:
    """基于 LangGraph Store 的长期记忆管理"""

    def __init__(self):
        self.store = InMemoryStore()

    def save_user_preference(self, user_id: str, key: str, value: Any):
        """保存用户偏好"""
        self.store.put(
            ["users", user_id, "preferences", key],
            value,
        )

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户所有偏好"""
        results = self.store.search(["users", user_id, "preferences"])
        return {item.key.split("/")[-1]: item.value for item in results}

    def save_conversation_summary(self, user_id: str, thread_id: str, summary: str):
        """保存对话摘要（用于跨会话记忆）"""
        import time
        self.store.put(
            ["users", user_id, "conversations", thread_id],
            {
                "summary": summary,
                "timestamp": time.time(),
            },
        )

    def get_recent_conversations(self, user_id: str, limit: int = 5):
        """获取最近的对话摘要"""
        items = self.store.search(["users", user_id, "conversations"])
        items.sort(key=lambda x: x.value.get("timestamp", 0), reverse=True)
        return items[:limit]


# 单例
user_memory = UserMemoryStore()
