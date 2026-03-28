"""
单元测试: backend/app/agents/editorial_room.py

测试范围:
- critique_node: 各 Agent 审查逻辑
- revision_node: 修订节点
- decision_node: 迭代决策逻辑
- EditorialRoom.review_and_revise: 端到端流程
"""

import json
import re
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.editorial_room import (
    EditorialState,
    EditorialRoom,
    critique_node,
    decision_node,
    revision_node,
    editorial_graph,
    get_llm,
)


class FakeLLMResponse:
    """模拟 LLM 返回的 JSON 格式响应"""

    def __init__(self, content: str):
        self.content = content


# --- Mock LLM 响应 ---

FAKE_PASS_RESPONSE_A = FakeLLMResponse(
    json.dumps({"score": 9.0, "critique": "逻辑严密，无问题", "suggestion": ""})
)
FAKE_PASS_RESPONSE_B = FakeLLMResponse(
    json.dumps({"score": 8.5, "critique": "爽点到位", "suggestion": ""})
)
FAKE_PASS_RESPONSE_C = FakeLLMResponse(
    json.dumps({"score": 8.0, "critique": "思想深刻", "suggestion": ""})
)

FAKE_FAIL_RESPONSE_A = FakeLLMResponse(
    json.dumps({"score": 6.0, "critique": "战力崩坏", "suggestion": "削弱主角实力"})
)
FAKE_FAIL_RESPONSE_B = FakeLLMResponse(
    json.dumps({"score": 5.5, "critique": "爽点不足", "suggestion": "增加打脸情节"})
)
FAKE_FAIL_RESPONSE_C = FakeLLMResponse(
    json.dumps({"score": 4.0, "critique": "偏离主题", "suggestion": "强化主题呼应"})
)


# --- Test Cases ---

class DecisionNodeTests(unittest.TestCase):
    """测试 decision_node 决策逻辑"""

    def test_end_when_all_scores_pass(self):
        """所有评分 >= 8 时应结束"""
        state: EditorialState = {
            "draft": "初稿内容",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": [],
            "scores": [9.0, 8.5, 8.0],
            "iteration_count": 0,
            "logs": [],
        }
        result = decision_node(state)
        self.assertEqual(result, "end")

    def test_continue_when_any_score_low(self):
        """任一评分 < 8 时应继续修订"""
        state: EditorialState = {
            "draft": "初稿内容",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": [],
            "scores": [9.0, 7.5, 8.0],
            "iteration_count": 0,
            "logs": [],
        }
        result = decision_node(state)
        self.assertEqual(result, "revise")

    def test_max_iterations_force_end(self):
        """迭代次数 >= 2 时强制结束"""
        state: EditorialState = {
            "draft": "初稿内容",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": [],
            "scores": [6.0, 5.5, 4.0],
            "iteration_count": 2,
            "logs": [],
        }
        result = decision_node(state)
        self.assertEqual(result, "end")

    def test_iteration_boundary_at_max(self):
        """iteration_count = 1 时可继续（最多修订2次）"""
        state: EditorialState = {
            "draft": "初稿内容",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": [],
            "scores": [6.0, 5.5, 4.0],
            "iteration_count": 1,
            "logs": [],
        }
        result = decision_node(state)
        self.assertEqual(result, "revise")

    def test_empty_scores_returns_end(self):
        """空评分列表时直接结束"""
        state: EditorialState = {
            "draft": "初稿内容",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": [],
            "scores": [],
            "iteration_count": 0,
            "logs": [],
        }
        result = decision_node(state)
        self.assertEqual(result, "end")

    def test_only_last_three_scores_matter(self):
        """决策只考虑最后3个评分"""
        # 前面的低分应被后面的高分覆盖
        state: EditorialState = {
            "draft": "初稿内容",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": [],
            "scores": [6.0, 7.0, 9.0, 9.0, 9.0],  # 最后3个都是高分
            "iteration_count": 0,
            "logs": [],
        }
        result = decision_node(state)
        self.assertEqual(result, "end")


class RevisionNodeTests(unittest.IsolatedAsyncioTestCase):
    """测试 revision_node 修订节点"""

    async def test_revision_increments_count(self):
        """修订后迭代计数应 +1"""
        state: EditorialState = {
            "draft": "初稿内容",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": ["问题1", "问题2"],
            "scores": [6.0, 5.5],
            "iteration_count": 0,
            "logs": [],
        }
        # Mock the chain
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=FakeLLMResponse("修订后的内容"))
        mock_prompt_template = MagicMock()
        mock_prompt_template.__or__ = MagicMock(return_value=mock_chain)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await revision_node(state)

        self.assertEqual(result["iteration_count"], 1)

    async def test_revision_cleans_think_tags(self):
        """修订应清除<think>标签"""
        state: EditorialState = {
            "draft": "<think>思考过程</think>正文内容",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": ["问题"],
            "scores": [6.0],
            "iteration_count": 0,
            "logs": [],
        }
        # Mock chain returns cleaned content (without think tags)
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=FakeLLMResponse("修订后的正文内容"))
        mock_prompt_template = MagicMock()
        mock_prompt_template.__or__ = MagicMock(return_value=mock_chain)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await revision_node(state)

        self.assertNotIn("<think>", result["draft"])
        self.assertNotIn("**", result["draft"])

    async def test_revision_removes_bold_markers(self):
        """修订应移除 ** 粗体标记"""
        state: EditorialState = {
            "draft": "**加粗文字**普通文字",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": ["问题"],
            "scores": [6.0],
            "iteration_count": 0,
            "logs": [],
        }
        # Mock chain returns cleaned content
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=FakeLLMResponse("<think>**都会被移除**</think>加粗文字普通文字"))
        mock_prompt_template = MagicMock()
        mock_prompt_template.__or__ = MagicMock(return_value=mock_chain)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await revision_node(state)

        self.assertNotIn("**", result["draft"])
        self.assertIn("加粗文字", result["draft"])

    async def test_revision_adds_log(self):
        """修订后应添加日志"""
        state: EditorialState = {
            "draft": "初稿",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": ["问题"],
            "scores": [6.0],
            "iteration_count": 0,
            "logs": [],
        }
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=FakeLLMResponse("修订内容"))
        mock_prompt_template = MagicMock()
        mock_prompt_template.__or__ = MagicMock(return_value=mock_chain)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await revision_node(state)

        self.assertEqual(len(result["logs"]), 1)
        self.assertIn("第 1 版修改", result["logs"][0])

    async def test_revision_adds_correct_version_log(self):
        """日志应显示正确的修订版本号"""
        state: EditorialState = {
            "draft": "初稿",
            "context": "上下文",
            "philosophical_theme": "天道酬勤",
            "critiques": ["问题"],
            "scores": [6.0],
            "iteration_count": 1,
            "logs": ["之前的日志"],
        }
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=FakeLLMResponse("修订内容"))
        mock_prompt_template = MagicMock()
        mock_prompt_template.__or__ = MagicMock(return_value=mock_chain)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await revision_node(state)

        self.assertIn("第 2 版修改", result["logs"][0])


class CritiqueNodeTests(unittest.IsolatedAsyncioTestCase):
    """测试 critique_node 审查节点"""

    def _make_mock_chain(self, response: FakeLLMResponse):
        """创建 mock chain"""
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=response)
        mock_prompt_template = MagicMock()
        mock_prompt_template.__or__ = MagicMock(return_value=mock_chain)
        return mock_prompt_template

    async def test_agent_a_returns_critique_and_score(self):
        """Agent A 应返回审查意见和评分"""
        state: EditorialState = {
            "draft": "战力体系测试内容",
            "context": "修仙世界观",
            "philosophical_theme": "天道酬勤",
            "critiques": [],
            "scores": [],
            "iteration_count": 0,
            "logs": [],
        }

        mock_prompt_template = self._make_mock_chain(FAKE_FAIL_RESPONSE_A)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await critique_node(state)

        self.assertIn("critiques", result)
        self.assertIn("scores", result)
        self.assertEqual(result["scores"][-1], 6.0)
        self.assertIn("战力崩坏", result["critiques"][-1])

    async def test_agent_b_punchline_review(self):
        """Agent B 应检查爽点"""
        state: EditorialState = {
            "draft": "期待感测试内容",
            "context": "都市爽文",
            "philosophical_theme": "逆袭人生",
            "critiques": [],
            "scores": [],
            "iteration_count": 0,
            "logs": [],
        }

        mock_prompt_template = self._make_mock_chain(FAKE_FAIL_RESPONSE_B)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await critique_node(state)

        self.assertEqual(result["scores"][-1], 5.5)
        self.assertIn("爽点不足", result["critiques"][-1])

    async def test_agent_c_philosophy_review(self):
        """Agent C 应检查思想深度"""
        state: EditorialState = {
            "draft": "哲学主题测试",
            "context": "古典文学",
            "philosophical_theme": "天道无情",
            "critiques": [],
            "scores": [],
            "iteration_count": 0,
            "logs": [],
        }

        mock_prompt_template = self._make_mock_chain(FAKE_FAIL_RESPONSE_C)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await critique_node(state)

        self.assertEqual(result["scores"][-1], 4.0)
        self.assertIn("偏离主题", result["critiques"][-1])

    async def test_critique_accumulates_scores(self):
        """critique_node 应累积所有 Agent 的评分（3个Agent并行）"""
        state1: EditorialState = {
            "draft": "初稿",
            "context": "上下文",
            "philosophical_theme": "主题",
            "critiques": [],
            "scores": [],
            "iteration_count": 0,
            "logs": [],
        }

        mock_prompt_template = self._make_mock_chain(FAKE_FAIL_RESPONSE_A)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result1 = await critique_node(state1)

        # 3个Agent并行运行，所以应该有3个评分
        self.assertEqual(len(result1["scores"]), 3)


class EditorialRoomIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """测试 EditorialRoom 端到端流程"""

    def _make_mock_chain(self, response: FakeLLMResponse):
        """创建 mock chain"""
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=response)
        mock_prompt_template = MagicMock()
        mock_prompt_template.__or__ = MagicMock(return_value=mock_chain)
        return mock_prompt_template

    async def test_review_and_revise_cleans_initial_draft(self):
        """初稿应被清理"""
        dirty_draft = "<think>思考中**加粗**</think>正文"

        # Mock chain returns cleaned content with high score
        mock_prompt_template = self._make_mock_chain(FAKE_PASS_RESPONSE_A)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await EditorialRoom.review_and_revise(
                draft=dirty_draft,
                context="上下文",
                philosophical_theme="主题"
            )

        # 清理后的内容不应包含think标签和粗体
        self.assertNotIn("<think>", result["content"])
        self.assertNotIn("**", result["content"])

    async def test_review_and_revise_adds_initial_log(self):
        """应包含初始提交日志"""
        mock_prompt_template = self._make_mock_chain(FAKE_PASS_RESPONSE_A)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await EditorialRoom.review_and_revise(
                draft="初稿",
                context="上下文",
                philosophical_theme="主题"
            )

        self.assertTrue(any("审稿委员会" in log for log in result["logs"]))

    async def test_review_and_revise_none_theme_handling(self):
        """philosophical_theme 为 None 时应使用默认值"""
        mock_prompt_template = self._make_mock_chain(FAKE_PASS_RESPONSE_A)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await EditorialRoom.review_and_revise(
                draft="初稿",
                context="上下文",
                philosophical_theme=None
            )

        # 不应抛出异常
        self.assertIn("content", result)

    async def test_review_and_revise_returns_final_scores(self):
        """应返回最终评分"""
        mock_prompt_template = self._make_mock_chain(FAKE_PASS_RESPONSE_A)

        with patch("app.agents.editorial_room.ChatPromptTemplate.from_template", return_value=mock_prompt_template):
            result = await EditorialRoom.review_and_revise(
                draft="初稿",
                context="上下文",
                philosophical_theme="主题"
            )

        self.assertIn("final_scores", result)


class ContentCleaningTests(unittest.TestCase):
    """测试内容清理逻辑"""

    def test_remove_think_tags(self):
        """应正确移除<think>标签"""
        content = "<think>思考过程</think>正文"
        clean = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        self.assertEqual(clean, "正文")

    def test_remove_multiline_think_tags(self):
        """应正确移除多行的<think>标签"""
        content = "<think>\n思考过程\n</think>正文"
        clean = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        self.assertEqual(clean, "正文")

    def test_remove_bold_markers(self):
        """应移除 ** 标记"""
        content = "**粗体**普通**再次粗体**文字"
        clean = re.sub(r'\*\*', '', content).strip()
        self.assertEqual(clean, "粗体普通再次粗体文字")

    def test_combined_cleaning(self):
        """组合清理测试"""
        content = "<think>思考**加粗**</think>**标记**正文"
        clean = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        clean = re.sub(r'\*\*', '', clean).strip()
        self.assertEqual(clean, "标记正文")


if __name__ == "__main__":
    unittest.main()
