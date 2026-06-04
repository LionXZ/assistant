# src/agent/assistant.py
from typing import Optional, AsyncIterator, Dict, Any
from langchain.agents import create_agent
from langchain.agents.middleware import (
    SummarizationMiddleware,
    ModelRetryMiddleware,
)
from langchain_core.messages import HumanMessage

from src.config.settings import settings
from src.models.chat_model import get_main_model, get_mini_model
from src.tools.registry import tool_registry
from src.tools.rag_tool import search_knowledge_base
from src.memory.checkpointer import get_checkpointer
from src.memory.store import user_memory
from src.middleware.custom import UserPreferenceMiddleware
from src.rag.retriever import rag_retriever


class DevAssistantAgent:
    """AI 编程助手 Agent"""

    def __init__(self):
        self.agent = None
        self._initialized = False

    async def initialize(self):
        """初始化 Agent（异步加载向量索引等）"""
        if self._initialized:
            return

        print("\n>>> 初始化 DevAssistant Agent...")

        # 1. 准备 RAG 检索器
        print("1. 加载知识库索引...")
        if not rag_retriever.load_index():
            print("  索引不存在，正在构建...")
            rag_retriever.build_index()

        # 2. 注册 RAG 工具
        tool_registry.add_tool(search_knowledge_base)

        # 3. 获取所有工具
        tools = tool_registry.get_all_tools()
        print(f"2. 已注册 {len(tools)} 个工具:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")

        # 4. 组装 Agent
        print("3. 组装 Agent...")
        self.agent = create_agent(
            # ===== 模型 =====
            model=get_main_model(temperature=0.7),

            # ===== 工具 =====
            tools=tools,

            # ===== 系统提示 =====
            system_prompt="""你是 DevAssistant，一个专业的 AI 编程助手。你的职责是：

1. **回答编程问题**：优先使用知识库搜索（search_knowledge_base）查找答案
2. **分析代码**：使用 read_code_file 读取代码并给出分析和建议
3. **搜索技术资料**：使用 web_search 查找最新的技术文档
4. **项目导航**：使用 list_code_files 了解项目结构

工作原则：
- 用中文回答，代码示例保持英文
- 回答包含可运行的代码示例
- 不确定时先搜索知识库，不要猜测
- 代码审查时按：bug > 性能 > 安全 > 可维护性 的优先级
- 每个建议都要说明原因""",

            # ===== 中间件 =====
            middleware=[
                SummarizationMiddleware(
                    model=get_mini_model(),
                    trigger=("tokens", 50000),   # DeepSeek 128K上下文, 超过50K时触发摘要
                    keep=("messages", 15),
                ),
                ModelRetryMiddleware(
                    max_retries=settings.MAX_MODEL_RETRIES,
                    backoff_factor=2.0,
                    initial_delay=1.0,
                ),
            ],

            # ===== 持久化 =====
            checkpointer=get_checkpointer(),

            # ===== 配置 =====
            name="dev_assistant",
            debug=settings.DEBUG,
        )

        self._initialized = True
        print("  ✓ Agent 初始化完成\n")

    async def chat(
        self,
        message: str,
        thread_id: str = "default",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """同步对话"""
        await self.initialize()

        scoped_thread = f"{user_id}:{thread_id}" if user_id else thread_id
        config = {"configurable": {"thread_id": scoped_thread}, "recursion_limit": 50}

        # 如果有用户偏好，临时添加偏好中间件
        middleware = []
        if user_id:
            middleware.append(UserPreferenceMiddleware(user_id))

        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config,
        )

        # 提取回复
        response = result["messages"][-1]
        return {
            "content": response.content,
            "thread_id": thread_id,
            "message_count": len(result["messages"]),
        }

    async def chat_stream(
        self,
        message: str,
        thread_id: str = "default",
        user_id: str = None,
    ) -> AsyncIterator[str]:
        """流式对话"""
        await self.initialize()

        # 按用户隔离 thread_id
        scoped_thread = f"{user_id}:{thread_id}" if user_id else thread_id
        config = {"configurable": {"thread_id": scoped_thread}, "recursion_limit": 50}

        async for event in self.agent.astream_events(
            {"messages": [{"role": "user", "content": message}]},
            config,
            version="v2",
        ):
            kind = event["event"]

            # 逐 token 输出
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content

            # 工具调用事件
            elif kind == "on_tool_start":
                yield f"\n\n🔧 **[调用工具: {event['name']}]**\n"

            elif kind == "on_tool_end":
                output = str(event["data"]["output"])[:200]
                yield f"\n📋 **[工具返回: {output}...]**\n\n"


# 全局单例
assistant = DevAssistantAgent()
