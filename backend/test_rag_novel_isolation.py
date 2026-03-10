# -*- coding: utf-8 -*-
"""RAG 按 novel_id 隔离的单元测试：验证检索结果仅来自指定小说。"""
import tempfile
import unittest
from app.rag.service import RAGService


class TestRAGNovelIsolation(unittest.TestCase):
    """测试 RAG retrieve_context 在传入 novel_id 时只返回该小说的知识。"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rag = RAGService(persist_directory=self.temp_dir)

    def test_retrieve_context_filters_by_novel_id(self):
        # 为小说 A 和 B 各写入一条场景摘要
        self.rag.add_knowledge(
            text="小说A第一章：主角进入青云宗，开始修炼。",
            doc_id="summary_novel_a_1",
            type="scene_summary",
            metadata={"novel_id": "novel-a", "scene_id": "s1", "chapter_id": "c1"},
        )
        self.rag.add_knowledge(
            text="小说B第一章：侦探接到案件，前往现场。",
            doc_id="summary_novel_b_1",
            type="scene_summary",
            metadata={"novel_id": "novel-b", "scene_id": "s2", "chapter_id": "c2"},
        )

        # 检索时限定 novel_id=novel-a，应只得到小说 A 的摘要
        results_a = self.rag.retrieve_context(
            query="主角修炼",
            type="scene_summary",
            top_k=5,
            novel_id="novel-a",
        )
        self.assertGreater(len(results_a), 0, "应至少有一条 novel-a 的结果")
        for r in results_a:
            self.assertEqual(
                r.get("metadata", {}).get("novel_id"),
                "novel-a",
                "结果应全部属于 novel-a",
            )

        # 限定 novel_id=novel-b，应只得到小说 B 的摘要
        results_b = self.rag.retrieve_context(
            query="侦探案件",
            type="scene_summary",
            top_k=5,
            novel_id="novel-b",
        )
        self.assertGreater(len(results_b), 0, "应至少有一条 novel-b 的结果")
        for r in results_b:
            self.assertEqual(
                r.get("metadata", {}).get("novel_id"),
                "novel-b",
                "结果应全部属于 novel-b",
            )

    def test_retrieve_context_with_novel_id_returns_no_results_for_other_novel(self):
        """传入 novel_id 时，不应返回其他小说的文档。"""
        self.rag.add_knowledge(
            text="仅属于小说X的内容。",
            doc_id="only_novel_x",
            type="scene_summary",
            metadata={"novel_id": "novel-x", "scene_id": "sx"},
        )

        results = self.rag.retrieve_context(
            query="仅属于小说X",
            type="scene_summary",
            top_k=5,
            novel_id="novel-y",
        )
        self.assertEqual(len(results), 0, "novel_id=novel-y 时不应命中 novel-x 的文档")
