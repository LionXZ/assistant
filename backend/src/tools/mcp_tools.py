# src/tools/mcp_tools.py
"""
MCP (Model Context Protocol) 工具集成

MCP 是一种标准化的工具协议，让 LangChain Agent 可以
无缝使用外部 MCP 服务器提供的工具。
"""
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import List
from langchain_core.tools import BaseTool


class MCPToolManager:
    """MCP 工具管理器"""

    def __init__(self):
        self.client = None
        self._tools: List[BaseTool] = []

    async def connect_stdio_server(self, name: str, command: str, args: List[str]):
        """连接 stdio 模式的 MCP 服务器"""
        if self.client is None:
            self.client = MultiServerMCPClient({})

        await self.client.connect_to_server(
            name,
            {
                "transport": "stdio",
                "command": command,
                "args": args,
            },
        )

    async def connect_http_server(self, name: str, url: str):
        """连接 HTTP 模式的 MCP 服务器"""
        if self.client is None:
            self.client = MultiServerMCPClient({})

        await self.client.connect_to_server(
            name,
            {
                "transport": "streamable_http",
                "url": url,
            },
        )

    async def load_tools(self) -> List[BaseTool]:
        """加载所有 MCP 服务器的工具"""
        if self.client:
            self._tools = await self.client.get_tools()
        return self._tools

    async def close(self):
        """关闭所有连接"""
        if self.client:
            await self.client.close()


# 使用示例
"""
# 连接数学计算 MCP 服务器
mcp_manager = MCPToolManager()
await mcp_manager.connect_stdio_server(
    name="math",
    command="python",
    args=["math_server.py"],
)
mcp_tools = await mcp_manager.load_tools()
"""
