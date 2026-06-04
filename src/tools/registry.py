# src/tools/registry.py
from typing import List
from langchain_core.tools import BaseTool
from src.tools.code_tools import read_code_file, list_code_files, count_code_lines
from src.tools.web_tools import web_search


class ToolRegistry:
    """工具注册中心：统一管理所有工具"""

    _instance = None
    _tools: List[BaseTool] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._register_defaults()
        return cls._instance

    def _register_defaults(self):
        """注册默认工具"""
        self._tools = [
            read_code_file,
            list_code_files,
            count_code_lines,
            web_search,
        ]

    def get_all_tools(self) -> List[BaseTool]:
        """获取所有已注册的工具"""
        return self._tools

    def add_tool(self, tool: BaseTool):
        """动态注册新工具"""
        self._tools.append(tool)

    def get_tool_by_name(self, name: str) -> BaseTool:
        """按名称获取工具"""
        for tool in self._tools:
            if tool.name == name:
                return tool
        raise ValueError(f"工具 '{name}' 未注册")


# 单例
tool_registry = ToolRegistry()
