import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.services import novel_usecases


class _FakeResult:
    def __init__(self, scalar=None, scalars=None):
        self._scalar = scalar
        self._scalars = scalars or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: self._scalars)


class NovelUsecasesTests(unittest.IsolatedAsyncioTestCase):
    async def test_update_rag_summary_for_novel_success(self):
        db = SimpleNamespace(execute=AsyncMock(return_value=_FakeResult(scalar=SimpleNamespace(id="n1"))))

        with patch.object(
            novel_usecases.rag_service,
            "retrieve_all_by_novel",
            new=MagicMock(
                return_value=[
                    {"id": "doc-1", "text": "old", "metadata": {"scene_id": "s1", "novel_id": "n1"}}
                ]
            ),
        ), patch.object(novel_usecases.rag_service, "add_knowledge", new=MagicMock()) as mock_add:
            result = await novel_usecases.update_rag_summary_for_novel("n1", "doc-1", "new", db)

        self.assertEqual(result, {"message": "Summary updated", "id": "doc-1"})
        mock_add.assert_called_once()
        kwargs = mock_add.call_args.kwargs
        self.assertEqual(kwargs["metadata"]["scene_id"], "s1")
        self.assertEqual(kwargs["text"], "new")

    async def test_update_rag_summary_for_novel_missing_summary(self):
        db = SimpleNamespace(execute=AsyncMock(return_value=_FakeResult(scalar=SimpleNamespace(id="n1"))))
        with patch.object(
            novel_usecases.rag_service,
            "retrieve_all_by_novel",
            new=MagicMock(return_value=[]),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await novel_usecases.update_rag_summary_for_novel("n1", "missing", "new", db)
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_delete_rag_summary_for_novel_success(self):
        db = SimpleNamespace(execute=AsyncMock(return_value=_FakeResult(scalar=SimpleNamespace(id="n1"))))
        with patch.object(novel_usecases.rag_service, "delete_knowledge", new=MagicMock()) as mock_delete:
            result = await novel_usecases.delete_rag_summary_for_novel("n1", "doc-1", db)
        self.assertEqual(result, {"message": "Summary deleted"})
        mock_delete.assert_called_once_with("doc-1", "scene_summary")

    async def test_build_novel_export_payload_success(self):
        novel = SimpleNamespace(id="n1", title="标题", premise="简介")
        chapter = SimpleNamespace(id="c1", order_index=1, title="开端")
        scenes = [
            SimpleNamespace(order_index=1, content="正文A", beat_description=None),
            SimpleNamespace(order_index=2, content=None, beat_description="细纲B"),
        ]

        db = SimpleNamespace(
            execute=AsyncMock(
                side_effect=[
                    _FakeResult(scalar=novel),
                    _FakeResult(scalars=[chapter]),
                    _FakeResult(scalars=scenes),
                ]
            )
        )

        payload = await novel_usecases.build_novel_export_payload("n1", db)
        self.assertIn("《标题》", payload["content"])
        self.assertIn("正文A", payload["content"])
        self.assertIn("细纲B", payload["content"])
        self.assertEqual(payload["filename"], "%E6%A0%87%E9%A2%98.txt")

    async def test_generate_novel_outline_for_novel_success(self):
        novel = SimpleNamespace(id="n1", premise=None, genre=None, tone=None)
        old_chapter = SimpleNamespace(id="old-c")
        old_character = SimpleNamespace(id="old-u")
        old_lore = SimpleNamespace(id="old-l")
        db = SimpleNamespace(
            execute=AsyncMock(
                side_effect=[
                    _FakeResult(scalar=novel),
                    _FakeResult(scalars=[old_chapter]),
                    _FakeResult(scalars=[old_character]),
                    _FakeResult(scalars=[old_lore]),
                ]
            ),
            commit=AsyncMock(),
            delete=AsyncMock(),
            add=MagicMock(),
            refresh=AsyncMock(),
        )

        with patch.object(
            novel_usecases.outline_generator,
            "generate_outline",
            new=AsyncMock(
                return_value={
                    "chapters": [{"id": "c1", "novel_id": "n1", "order_index": 1, "title": "t1", "summary": "s1"}],
                    "characters": [{"id": "u1", "name": "a"}],
                    "lore": [{"id": "l1", "title": "设定", "content": "x"}],
                }
            ),
        ):
            chapters = await novel_usecases.generate_novel_outline_for_novel(
                novel_id="n1",
                premise="p",
                genre="g",
                tone="t",
                num_chapters=10,
                db=db,
            )

        self.assertEqual(len(chapters), 1)
        self.assertEqual(novel.premise, "p")
        self.assertEqual(novel.genre, "g")
        self.assertEqual(novel.tone, "t")
        self.assertEqual(db.commit.await_count, 3)
        self.assertEqual(db.delete.await_count, 3)

    async def test_generate_novel_outline_for_novel_not_found(self):
        db = SimpleNamespace(execute=AsyncMock(return_value=_FakeResult(scalar=None)))
        with self.assertRaises(HTTPException) as ctx:
            await novel_usecases.generate_novel_outline_for_novel(
                novel_id="missing",
                premise="p",
                genre="g",
                tone="t",
                num_chapters=10,
                db=db,
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_generate_novel_outline_for_novel_generator_error(self):
        novel = SimpleNamespace(id="n1", premise=None, genre=None, tone=None)
        db = SimpleNamespace(
            execute=AsyncMock(
                side_effect=[
                    _FakeResult(scalar=novel),
                    _FakeResult(scalars=[]),
                    _FakeResult(scalars=[]),
                    _FakeResult(scalars=[]),
                ]
            ),
            commit=AsyncMock(),
            delete=AsyncMock(),
            add=MagicMock(),
            refresh=AsyncMock(),
        )
        with patch.object(
            novel_usecases.outline_generator,
            "generate_outline",
            new=AsyncMock(side_effect=ValueError("boom")),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await novel_usecases.generate_novel_outline_for_novel(
                    novel_id="n1",
                    premise="p",
                    genre="g",
                    tone="t",
                    num_chapters=10,
                    db=db,
                )
        self.assertEqual(ctx.exception.status_code, 500)


if __name__ == "__main__":
    unittest.main()
