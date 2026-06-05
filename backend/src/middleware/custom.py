# src/middleware/custom.py
import time
import logging
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState
from langchain_core.messages import SystemMessage
from backend.src.memory.store import user_memory

logger = logging.getLogger(__name__)


class UserPreferenceMiddleware(AgentMiddleware):
    """将用户偏好注入到系统消息中"""

    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id

    def before_agent(self, state: AgentState, runtime) -> dict | None:
        prefs = user_memory.get_user_preferences(self.user_id)

        if prefs:
            pref_lines = ["\n用户偏好设置："]
            for k, v in prefs.items():
                pref_lines.append(f"- {k}: {v}")

            # 在消息列表开头添加偏好信息
            pref_msg = SystemMessage(content="\n".join(pref_lines))
            state["messages"].insert(0, pref_msg)

        return None  # 不修改状态，继续执行


class PerformanceMonitorMiddleware(AgentMiddleware):
    """记录每次模型调用和工具调用的耗时"""

    def __init__(self):
        super().__init__()
        self.model_calls = []
        self.tool_calls = []

    async def wrap_model_call(self, request, handler):
        start = time.time()
        response = await handler(request)
        elapsed = time.time() - start

        self.model_calls.append({
            "model": request.model_name,
            "time": elapsed,
            "tokens": getattr(response, "usage_metadata", {}),
        })

        logger.info(f"模型调用: {request.model_name}, 耗时: {elapsed:.2f}s")

        return response

    async def wrap_tool_call(self, request, handler):
        start = time.time()
        response = await handler(request)
        elapsed = time.time() - start

        self.tool_calls.append({
            "tool": request.tool_call.get("name", "unknown"),
            "time": elapsed,
        })

        logger.info(f"工具调用: {request.tool_call.get('name')}, 耗时: {elapsed:.2f}s")

        return response

    def after_agent(self, state: AgentState, runtime) -> dict | None:
        total_model_time = sum(c["time"] for c in self.model_calls)
        total_tool_time = sum(c["time"] for c in self.tool_calls)

        logger.info(
            f"Agent 执行完毕: "
            f"模型调用 {len(self.model_calls)} 次 ({total_model_time:.2f}s), "
            f"工具调用 {len(self.tool_calls)} 次 ({total_tool_time:.2f}s)"
        )
        return None
