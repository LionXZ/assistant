# tests/test_agent.py
import pytest
import asyncio
from src.agent.assistant import assistant


@pytest.mark.asyncio
async def test_agent_basic_chat():
    """测试 Agent 基本对话"""
    await assistant.initialize()

    result = await assistant.chat(
        message="你好，请用一句话介绍自己",
        thread_id="test-basic-001",
    )

    assert result["content"]
    assert result["thread_id"] == "test-basic-001"
    assert result["message_count"] > 0


@pytest.mark.asyncio
async def test_agent_multi_turn():
    """测试多轮对话"""
    await assistant.initialize()
    thread_id = "test-multi-001"

    # 第一轮：告诉 Agent 偏好
    await assistant.chat(
        message="我偏好使用 TypeScript",
        thread_id=thread_id,
        user_id="test-user",
    )

    # 第二轮：Agent 应记住偏好
    result = await assistant.chat(
        message="推荐一个 Web 框架",
        thread_id=thread_id,
        user_id="test-user",
    )

    assert result["content"]
    assert result["message_count"] > 2  # 累积消息
