import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import scene_postprocess


class _FakeResult:
    def __init__(self, row=None):
        self._row = row

    def first(self):
        return self._row


class _AsyncSessionCtx:
    def __init__(self, db):
        self._db = db

    async def __aenter__(self):
        return self._db

    async def __aexit__(self, exc_type, exc, tb):
        return False


class ScenePostprocessTests(unittest.IsolatedAsyncioTestCase):
    async def test_summarize_scene_success(self):
        scene = SimpleNamespace(content="正文", summary=None)
        chapter = SimpleNamespace(id="c1", novel_id="n1")
        db = SimpleNamespace(
            execute=AsyncMock(return_value=_FakeResult(row=(scene, chapter))),
            commit=AsyncMock(),
        )

        with patch.object(
            scene_postprocess,
            "AsyncSessionLocal",
            return_value=_AsyncSessionCtx(db),
        ), patch.object(
            scene_postprocess.summarizer,
            "generate_summary",
            new=AsyncMock(return_value="摘要"),
        ) as mock_summary, patch.object(
            scene_postprocess.rag_service,
            "add_knowledge",
            new=MagicMock(),
        ) as mock_add:
            await scene_postprocess.summarize_scene("scene-1")

        mock_summary.assert_awaited_once_with("正文")
        db.commit.assert_awaited_once()
        mock_add.assert_called_once()

    async def test_update_scene_summary_in_rag_success(self):
        chapter = SimpleNamespace(id="c1", novel_id="n1")
        db = SimpleNamespace(execute=AsyncMock(return_value=_FakeResult(row=(None, chapter))))

        with patch.object(
            scene_postprocess,
            "AsyncSessionLocal",
            return_value=_AsyncSessionCtx(db),
        ), patch.object(
            scene_postprocess.rag_service,
            "add_knowledge",
            new=MagicMock(),
        ) as mock_add:
            await scene_postprocess.update_scene_summary_in_rag("scene-1", "手动摘要")

        mock_add.assert_called_once()
        kwargs = mock_add.call_args.kwargs
        self.assertEqual(kwargs["metadata"]["novel_id"], "n1")
        self.assertEqual(kwargs["text"], "手动摘要")

    async def test_analyze_state_and_relationships_scene_not_found(self):
        db = SimpleNamespace(execute=AsyncMock(return_value=_FakeResult(row=None)), commit=AsyncMock())

        with patch.object(
            scene_postprocess,
            "AsyncSessionLocal",
            return_value=_AsyncSessionCtx(db),
        ):
            await scene_postprocess.analyze_state_and_relationships("missing")

        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
