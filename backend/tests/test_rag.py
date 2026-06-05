# tests/test_rag.py
import pytest
from backend.src.rag.retriever import rag_retriever
from backend.src.rag.loader import DocumentLoader
from backend.src.rag.splitter import DocumentSplitter


def test_document_splitter():
    """测试文档切分"""
    from langchain_core.documents import Document

    docs = [Document(page_content="这是一个测试文档。" * 100)]
    splitter = DocumentSplitter(chunk_size=100, chunk_overlap=20)
    chunks = splitter.split(docs)
    assert len(chunks) > 1


def test_document_loader_unsupported_format():
    """测试不支持的格式"""
    with pytest.raises(ValueError):
        DocumentLoader.load_file("test.unsupported")
