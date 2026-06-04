# src/rag/retriever.py
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from src.rag.loader import DocumentLoader
from src.rag.splitter import DocumentSplitter
from src.rag.embedder import get_embeddings
from src.config.settings import settings


class RAGRetriever:
    """RAG 检索器：加载 → 切分 → 嵌入 → 检索"""

    def __init__(self):
        self.embeddings = get_embeddings()
        self.vector_store: Optional[Chroma] = None

    def build_index(self, documents_dir: str = None, force_rebuild: bool = False):
        """构建向量索引"""
        if documents_dir is None:
            from src.config.settings import PROJECT_ROOT
            documents_dir = str(PROJECT_ROOT / "data" / "documents")

        print(f"\n>>> 构建 RAG 索引: {documents_dir}")

        # 1. 加载文档
        print("1. 加载文档...")
        docs = DocumentLoader.load_directory(documents_dir)
        if not docs:
            print("  ⚠ 未找到任何文档，跳过索引构建")
            return
        print(f"  总计: {len(docs)} 个文档")

        # 2. 切分
        print("2. 切分文档...")
        splitter = DocumentSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split(docs)

        # 3. 构建向量存储
        print("3. 构建向量索引...")
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR,
            collection_name="dev_docs",
        )
        print(f"  ✓ 索引构建完成，存储于: {settings.CHROMA_PERSIST_DIR}")

    def load_index(self):
        """加载已有索引"""
        import os
        if os.path.exists(settings.CHROMA_PERSIST_DIR):
            self.vector_store = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings,
                collection_name="dev_docs",
            )
            print(f"  ✓ 已加载索引: {self.vector_store._collection.count()} 个向量")
            return True
        return False

    def as_retriever(self, k: int = 5) -> BaseRetriever:
        """返回 LangChain 检索器"""
        if self.vector_store is None:
            raise RuntimeError("请先调用 build_index() 或 load_index()")
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )

    def search(self, query: str, k: int = 5) -> List[Document]:
        """搜索相关文档"""
        if self.vector_store is None:
            raise RuntimeError("请先调用 build_index() 或 load_index()")
        return self.vector_store.similarity_search(query, k=k)

    def add_file(self, filepath: str) -> int:
        """
        增量添加单个文件到索引。
        返回新增的 chunk 数量。
        """
        print(f"  📄 处理文件: {filepath}")
        docs = DocumentLoader.load_file(filepath)

        splitter = DocumentSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split(docs)
        print(f"     → {len(chunks)} 个文本块")

        if self.vector_store is None:
            # 首次添加: 新建索引
            print("     首次添加，创建新索引...")
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIR,
                collection_name="dev_docs",
            )
        else:
            # 已有索引: 增量追加
            self.vector_store.add_documents(chunks)

        print(f"  ✓ 已添加，当前索引共 {self.vector_store._collection.count()} 个向量")
        return len(chunks)

    def has_index(self) -> bool:
        """检查是否已有索引"""
        import os
        return os.path.exists(settings.CHROMA_PERSIST_DIR) and self.vector_store is not None


# 单例
rag_retriever = RAGRetriever()
