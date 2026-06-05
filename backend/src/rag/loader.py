# src/rag/loader.py
from pathlib import Path
from typing import List
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
)
from langchain_core.documents import Document


class DocumentLoader:
    """多格式文档加载器"""

    LOADERS = {
        ".txt": TextLoader,
        ".md": TextLoader,
        ".pdf": PyPDFLoader,
    }

    @classmethod
    def load_directory(cls, directory: str) -> List[Document]:
        """加载目录下所有支持的文档"""
        path = Path(directory)
        all_docs = []

        for file_path in path.rglob("*"):
            if file_path.suffix in cls.LOADERS:
                loader_cls = cls.LOADERS[file_path.suffix]
                try:
                    loader = loader_cls(str(file_path))
                    docs = loader.load()
                    # 添加来源元数据
                    for doc in docs:
                        doc.metadata["source"] = str(file_path.relative_to(path))
                    all_docs.extend(docs)
                    print(f"  ✓ 已加载: {file_path.name}")
                except Exception as e:
                    print(f"  ✗ 加载失败 {file_path.name}: {e}")

        return all_docs

    @classmethod
    def load_file(cls, filepath: str) -> List[Document]:
        """加载单个文件"""
        path = Path(filepath)
        if path.suffix not in cls.LOADERS:
            raise ValueError(f"不支持的文件格式: {path.suffix}")
        loader = cls.LOADERS[path.suffix](str(path))
        return loader.load()
