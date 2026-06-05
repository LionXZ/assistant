# src/rag/splitter.py
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class DocumentSplitter:
    """智能文档切分"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators or [
                "\n\n",     # 段落
                "\n",       # 行
                ". ",       # 句子
                " ",        # 单词
                "",         # 字符
            ],
            length_function=len,
        )

    def split(self, documents: List[Document]) -> List[Document]:
        """切分文档"""
        chunks = self.splitter.split_documents(documents)
        print(f"  ✓ 切分完成: {len(documents)} 个文档 → {len(chunks)} 个片段")
        return chunks
