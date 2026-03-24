import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import BackgroundTasks, HTTPException

from app.models.scene_version import SceneVersion
from app.services import scene_usecases


class _FakeResult:
    def __init__(self, row=None, scalar=None):
        self._row = row
        self._scalar = scalar

    def first(self):
        return self._row

    def scalar_one_or_none(self):
        return self._scalar


class SceneUsecasesTests(unittest.IsolatedAsyncioTestCase):
    async def test_summarize_scene_content_success(self):
        scene = SimpleNamespace(content="正文", summary=None)
        chapter = SimpleNamespace(id="chapter-1", novel_id="novel-1")
        db = SimpleNamespace(
            execute=AsyncMock(return_value=_FakeResult(row=(scene, chapter))),
            commit=AsyncMock(),
        )
        fake_config = SimpleNamespace(summary_model="test-model")

        with patch.object(
            scene_usecases.summarizer,
            "generate_summary",
            new=AsyncMock(return_value="摘要"),
        ) as mock_summary, patch.object(
            scene_usecases.rag_service, "add_knowledge", new=MagicMock()
        ) as mock_add, patch.object(
            scene_usecases, "get_llm_config_from_db", new=AsyncMock(return_value=fake_config)
        ):
            result = await scene_usecases.summarize_scene_content("scene-1", db)

        self.assertEqual(result, {"scene_id": "scene-1", "summary": "摘要"})
        self.assertEqual(scene.summary, "摘要")
        mock_summary.assert_awaited_once_with("正文", model_override="test-model")
        db.commit.assert_awaited_once()
        mock_add.assert_called_once()
        metadata = mock_add.call_args.kwargs["metadata"]
        self.assertEqual(metadata["novel_id"], "novel-1")
        self.assertEqual(metadata["chapter_id"], "chapter-1")

    async def test_summarize_scene_content_not_found(self):
        db = SimpleNamespace(
            execute=AsyncMock(return_value=_FakeResult(row=None)),
            commit=AsyncMock(),
        )
        with self.assertRaises(HTTPException) as ctx:
            await scene_usecases.summarize_scene_content("missing", db)
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_update_scene_schedules_summary_and_analysis(self):
        scene = SimpleNamespace(summary=None, content="", id="scene-1")
        db = SimpleNamespace(
            execute=AsyncMock(return_value=_FakeResult(scalar=scene)),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        background_tasks = BackgroundTasks()

        updated = await scene_usecases.update_scene_and_schedule_tasks(
            scene_id="scene-1",
            scene_update_data={"content": "x" * 201},
            background_tasks=background_tasks,
            db=db,
        )

        self.assertIs(updated, scene)
        funcs = [task.func for task in background_tasks.tasks]
        self.assertIn(scene_usecases.summarize_scene, funcs)
        self.assertIn(scene_usecases.analyze_state_and_relationships, funcs)

    async def test_update_scene_manual_summary_schedules_rag_update(self):
        scene = SimpleNamespace(summary="manual-summary", content="", id="scene-1")
        db = SimpleNamespace(
            execute=AsyncMock(return_value=_FakeResult(scalar=scene)),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        background_tasks = BackgroundTasks()

        await scene_usecases.update_scene_and_schedule_tasks(
            scene_id="scene-1",
            scene_update_data={"summary": "manual-summary"},
            background_tasks=background_tasks,
            db=db,
        )

        funcs = [task.func for task in background_tasks.tasks]
        self.assertIn(scene_usecases.update_scene_summary_in_rag, funcs)
        self.assertIn(scene_usecases.analyze_state_and_relationships, funcs)

    async def test_update_scene_empty_summary_does_not_schedule_rag_update(self):
        scene = SimpleNamespace(summary="", content="", id="scene-1")
        db = SimpleNamespace(
            execute=AsyncMock(return_value=_FakeResult(scalar=scene)),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        background_tasks = BackgroundTasks()

        await scene_usecases.update_scene_and_schedule_tasks(
            scene_id="scene-1",
            scene_update_data={"summary": ""},
            background_tasks=background_tasks,
            db=db,
        )

        self.assertEqual(len(background_tasks.tasks), 0)

    async def test_update_scene_saves_version_when_content_changes(self):
        """更新场景正文且与旧内容不同时，应写入一条历史版本。"""
        scene = SimpleNamespace(id="scene-1", content="old content", summary=None)
        call_count = [0]

        async def mock_execute(stmt):
            call_count[0] += 1
            if call_count[0] == 1:
                return _FakeResult(scalar=scene)
            r = MagicMock()
            r.all.return_value = []
            return r
        db = SimpleNamespace(
            execute=AsyncMock(side_effect=mock_execute),
            add=MagicMock(),
            flush=AsyncMock(),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        background_tasks = BackgroundTasks()

        await scene_usecases.update_scene_and_schedule_tasks(
            scene_id="scene-1",
            scene_update_data={"content": "new content"},
            background_tasks=background_tasks,
            db=db,
        )

        self.assertEqual(scene.content, "new content")
        self.assertGreaterEqual(db.add.call_count, 1, "应至少 add 一次 SceneVersion")
        call_args = [c[0][0] for c in db.add.call_args_list]
        version_adds = [a for a in call_args if isinstance(a, SceneVersion)]
        self.assertEqual(len(version_adds), 1)
        self.assertEqual(version_adds[0].content, "old content")
        self.assertEqual(version_adds[0].scene_id, "scene-1")


if __name__ == "__main__":
    unittest.main()
