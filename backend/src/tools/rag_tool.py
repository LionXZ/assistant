# src/tools/rag_tool.py
"""将检索器包装为 Agent 可用的工具"""
from langchain.tools import tool
from backend.src.rag.retriever import rag_retriever


@tool
def search_knowledge_base(query: str) -> str:
    """在编程知识库中搜索答案。用于查找编程语言用法、最佳实践、设计模式等技术内容。

    Args:
        query: 搜索关键词或问题，如 'Python 装饰器的用法'、'Go的错误处理最佳实践'
    """
    try:
        docs = rag_retriever.search(query, k=4)

        if not docs:
            return f"知识库中未找到关于 '{query}' 的相关内容"

        results = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知来源")
            content = doc.page_content[:500]
            results.append(f"[{i}] 来源: {source}\n{content}\n")

        return "\n".join(results)

    except Exception as e:
        return f"知识库搜索失败：{str(e)}"
