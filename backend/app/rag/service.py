"""RAG Service - 向量检索服务"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
from app.config import settings


class RAGService:
    """RAG 服务类 - 管理向量数据库"""

    def __init__(self):
        """初始化 ChromaDB 客户端"""
        persist_dir = settings.chromadb_persist_directory
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_dir)
        self._init_collections()

    def _init_collections(self):
        """初始化集合"""
        # 角色集合
        self.characters_collection = self.client.get_or_create_collection(
            name="characters",
            metadata={"description": "角色信息"}
        )

        # 世界观集合
        self.lore_collection = self.client.get_or_create_collection(
            name="lore",
            metadata={"description": "世界观设定"}
        )

        # 场景摘要集合
        self.summaries_collection = self.client.get_or_create_collection(
            name="scene_summaries",
            metadata={"description": "场景摘要"}
        )

    def add_knowledge(
        self,
        text: str,
        doc_id: str,
        type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        添加知识到向量数据库

        Args:
            text: 要向量化的文本
            doc_id: 文档 ID
            type: 类型 (character/lore/summary)
            metadata: 附加元数据
        """
        collection = self._get_collection(type)

        meta = metadata or {}
        meta["type"] = type

        collection.upsert(
            documents=[text],
            ids=[doc_id],
            metadatas=[meta]
        )

    def retrieve_context(
        self,
        query: str,
        type: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        根据查询检索相关上下文

        Args:
            query: 查询文本
            type: 要检索的类型 (character/lore/summary)
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        collection = self._get_collection(type)

        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )

        return self._format_results(results)

    def retrieve_all_by_novel(
        self,
        novel_id: str,
        type: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        检索某个小说相关的所有知识

        Args:
            novel_id: 小说 ID
            type: 类型
            top_k: 返回数量

        Returns:
            检索结果
        """
        collection = self._get_collection(type)

        results = collection.get(
            where={"novel_id": novel_id}
        )

        # 简单返回所有匹配的文档
        formatted = []
        if results.get("documents"):
            for i, doc in enumerate(results["documents"]):
                formatted.append({
                    "id": results["ids"][i],
                    "text": doc,
                    "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                })

        return formatted[:top_k]

    def _get_collection(self, type: str):
        """根据类型获取对应的集合"""
        collections = {
            "character": self.characters_collection,
            "characters": self.characters_collection,
            "lore": self.lore_collection,
            "summary": self.summaries_collection,
            "scene_summary": self.summaries_collection,
        }
        if type not in collections:
            raise ValueError(f"Unknown type: {type}. Available: {list(collections.keys())}")
        return collections[type]

    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """格式化检索结果"""
        formatted = []

        if not results.get("documents"):
            return formatted

        for i in range(len(results["documents"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None,
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {}
            })

        return formatted

    def delete_knowledge(self, doc_id: str, type: str):
        """删除知识"""
        collection = self._get_collection(type)
        collection.delete(ids=[doc_id])

    def clear_collection(self, type: str):
        """清空集合"""
        collection = self._get_collection(type)
        collection.delete(where={})


# 全局单例
rag_service = RAGService()
