# src/tools/web_tools.py
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Optional

# 如果安装了 tavily
try:
    from tavily import TavilyClient
    from backend.src.config.settings import settings
    _tavily = TavilyClient(api_key=settings.TAVILY_API_KEY) if settings.TAVILY_API_KEY else None
except ImportError:
    _tavily = None


class SearchInput(BaseModel):
    """搜索参数"""
    query: str = Field(description="搜索关键词")
    max_results: int = Field(default=5, description="最大结果数")


@tool(args_schema=SearchInput)
def web_search(query: str, max_results: int = 5) -> str:
    """在互联网上搜索技术文档和编程资料。

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数
    """
    if _tavily is None:
        return "搜索服务未配置（缺少 TAVILY_API_KEY）"

    try:
        response = _tavily.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_domains=["github.com", "stackoverflow.com", "docs.python.org", "go.dev"],
        )

        if not response.get("results"):
            return f"未找到关于 '{query}' 的相关结果"

        results = []
        for i, result in enumerate(response["results"], 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            content = result.get("content", "")[:300]
            results.append(f"{i}. {title}\n   链接: {url}\n   摘要: {content}\n")

        return "\n".join(results)

    except Exception as e:
        return f"搜索失败：{str(e)}"
