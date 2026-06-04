# tests/test_tools.py
import pytest
from src.tools.code_tools import read_code_file, list_code_files


def test_read_code_file_exists():
    """测试读取存在的文件"""
    result = read_code_file.invoke({"filepath": "src/tools/code_tools.py"})
    assert "错误" not in result
    assert len(result) > 0


def test_read_code_file_not_exists():
    """测试读取不存在的文件"""
    result = read_code_file.invoke({"filepath": "/nonexistent/file.py"})
    assert "错误" in result


def test_list_code_files():
    """测试列出文件"""
    result = list_code_files.invoke({"directory": "src", "pattern": "*.py"})
    assert "错误" not in result
    assert ".py" in result
