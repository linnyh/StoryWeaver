import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.services import chapter_usecases


class _FakeResult:
    def __init__(self, scalar=None, scalars=None):
        self._scalar = scalar
        self._scalars = scalars or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: self._scalars)


class ChapterUsecasesTests(unittest.IsolatedAsyncioTestCase):
    async def test_summarize_chapter_content_success(self):
        chapter = SimpleNamespace(id="chapter-1", title="第1章", summary=None)
        scenes = [
            SimpleNamespace(order_index=1, summary="scene sum", content=None, beat_description=None),
            SimpleNamespace(order_index=2, summary=None, content="scene content", beat_description=None),
        ]
        db = SimpleNamespace(
            execute=AsyncMock(
                side_effect=[
                    _FakeResult(scalar=chapter),
                    _FakeResult(scalars=scenes),
                ]
            ),
            commit=AsyncMock(),
        )

        with patch.object(
            chapter_usecases.scene_generator.llm,
            "generate",
            new=AsyncMock(return_value="<think>x</think>最终摘要"),
        ):
            result = await chapter_usecases.summarize_chapter_content("chapter-1", db)

        self.assertEqual(result["id"], "chapter-1")
        self.assertEqual(result["summary"], "最终摘要")
        self.assertEqual(chapter.summary, "最终摘要")
        db.commit.assert_awaited_once()

    async def test_summarize_chapter_content_no_chapter(self):
        db = SimpleNamespace(execute=AsyncMock(return_value=_FakeResult(scalar=None)))
        with self.assertRaises(HTTPException) as ctx:
            await chapter_usecases.summarize_chapter_content("missing", db)
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_summarize_chapter_content_no_scenes(self):
        chapter = SimpleNamespace(id="chapter-1", title="第1章", summary=None)
        db = SimpleNamespace(
            execute=AsyncMock(
                side_effect=[
                    _FakeResult(scalar=chapter),
                    _FakeResult(scalars=[]),
                ]
            )
        )
        with self.assertRaises(HTTPException) as ctx:
            await chapter_usecases.summarize_chapter_content("chapter-1", db)
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
