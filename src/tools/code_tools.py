# src/tools/code_tools.py
import os
import glob
from pathlib import Path
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional


class ReadFileInput(BaseModel):
    """读取文件的参数"""
    filepath: str = Field(description="文件路径（绝对路径或相对路径）")
    start_line: Optional[int] = Field(default=None, description="起始行号（可选，从1开始）")
    end_line: Optional[int] = Field(default=None, description="结束行号（可选，包含此行）")


@tool(args_schema=ReadFileInput)
def read_code_file(filepath: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """读取代码文件内容。支持指定行号范围。

    Args:
        filepath: 文件路径
        start_line: 可选，起始行号
        end_line: 可选，结束行号
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return f"错误：文件不存在 - {filepath}"

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if start_line is None:
            start_line = 1
        if end_line is None:
            end_line = len(lines)

        selected = lines[start_line - 1:end_line]
        result = "".join(selected)

        if len(result) > 8000:
            result = result[:8000] + "\n\n... (文件过长，已截断)"

        return result

    except Exception as e:
        return f"读取文件失败：{str(e)}"


class ListFilesInput(BaseModel):
    """列出文件的参数"""
    directory: str = Field(description="目录路径")
    pattern: str = Field(default="*", description="文件匹配模式，如 '*.py', '*.go'")


@tool(args_schema=ListFilesInput)
def list_code_files(directory: str, pattern: str = "*") -> str:
    """列出指定目录下的代码文件。支持通配符过滤。

    Args:
        directory: 目录路径
        pattern: 文件匹配模式，如 '*.py'
    """
    try:
        path = Path(directory)
        if not path.exists():
            return f"错误：目录不存在 - {directory}"

        if not path.is_dir():
            return f"错误：不是目录 - {directory}"

        files = list(path.rglob(pattern))
        # 排除常见非代码目录
        exclude_dirs = {"node_modules", "__pycache__", ".git", "venv", ".venv", "dist", "build"}
        files = [f for f in files if not any(ex in f.parts for ex in exclude_dirs)]

        if not files:
            return f"目录 {directory} 中没有匹配 {pattern} 的文件"

        result = []
        for f in sorted(files)[:50]:  # 最多 50 个
            size = f.stat().st_size
            result.append(f"  {f.relative_to(path)}  ({_format_size(size)})")

        return f"找到 {len(result)} 个文件:\n" + "\n".join(result)

    except Exception as e:
        return f"列出文件失败：{str(e)}"


@tool
def count_code_lines(filepath: str) -> str:
    """统计代码文件的行数、注释行数、空行数。

    Args:
        filepath: 文件路径
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return f"错误：文件不存在 - {filepath}"

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total = len(lines)
        empty = sum(1 for l in lines if l.strip() == "")
        comment = sum(1 for l in lines if l.strip().startswith(("#", "//", "--")))
        code = total - empty - comment

        return f"""
文件: {path.name}
总行数: {total}
代码行: {code} ({code/total*100:.1f}%)
注释行: {comment} ({comment/total*100:.1f}%)
空行: {empty} ({empty/total*100:.1f}%)
"""

    except Exception as e:
        return f"统计失败：{str(e)}"


def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
