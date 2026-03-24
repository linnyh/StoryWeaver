# -*- coding: utf-8 -*-
"""场景生成 SSE 流与场景版本 API 的集成测试。"""
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.database import init_db, AsyncSessionLocal
from app.models import Novel, Chapter, Scene
from app.main import app


async def _create_scene_in_db():
    """在测试库中创建一本小说、一章、一个场景，返回 scene_id。"""
    async with AsyncSessionLocal() as db:
        n = Novel(title="SSE Test Novel", premise="Test", genre="玄幻", tone="严肃")
        db.add(n)
        await db.commit()
        await db.refresh(n)
        ch = Chapter(novel_id=n.id, order_index=0, title="Ch1")
        db.add(ch)
        await db.commit()
        await db.refresh(ch)
        sc = Scene(chapter_id=ch.id, order_index=0, location="Test", content="")
        db.add(sc)
        await db.commit()
        await db.refresh(sc)
        return sc.id


class TestSceneSSEAndVersions(unittest.IsolatedAsyncioTestCase):
    """场景生成 SSE 与版本列表/恢复的集成测试。"""

    async def asyncSetUp(self):
        await init_db()
        self.scene_id = await _create_scene_in_db()
        transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_scene_generate_sse_returns_stream_with_chunk_and_done(self):
        """GET /api/scenes/{id}/generate 应返回 SSE 流，且包含 chunk 与 done 事件。"""
        async def fake_generate(*args, **kwargs):
            yield {"type": "system", "content": "starting"}
            yield {"type": "content", "content": "Hello"}
            yield {"type": "content", "content": " world."}

        with patch("app.api.scene.scene_generator.generate_scene_content", side_effect=fake_generate), \
             patch("app.api.settings.get_llm_config_from_db", new_callable=AsyncMock) as mock_cfg:
            mock_cfg.return_value = type("C", (), {"writing_model": "m", "editorial_model": "m"})()

            response = await self.client.get(
                f"/api/scenes/{self.scene_id}/generate",
                timeout=10.0,
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers.get("content-type", ""))

        text = response.text
        self.assertIn("data: ", text)
        # 应出现 chunk 与 done
        lines = [line.strip() for line in text.split("\n") if line.strip().startswith("data:")]
        data_lines = [json.loads(line.replace("data: ", "")) for line in lines if line.startswith("data:")]
        has_chunk = any("chunk" in d for d in data_lines)
        has_done = any(d.get("done") is True for d in data_lines)
        self.assertTrue(has_chunk, "SSE 流应包含 chunk 事件")
        self.assertTrue(has_done, "SSE 流应包含 done 事件")

    async def test_scene_versions_list_and_restore(self):
        """更新场景内容后应有历史版本；恢复版本后内容应还原。"""
        # 先更新一次内容，产生一条历史版本（当前空 -> "v1" 不产生版本；再 "v1" -> "v2" 产生 v1）
        await self.client.put(
            f"/api/scenes/{self.scene_id}",
            json={"content": "first content"},
        )
        await self.client.put(
            f"/api/scenes/{self.scene_id}",
            json={"content": "second content"},
        )

        versions_resp = await self.client.get(f"/api/scenes/{self.scene_id}/versions")
        self.assertEqual(versions_resp.status_code, 200)
        versions = versions_resp.json()
        self.assertIsInstance(versions, list)
        self.assertGreaterEqual(len(versions), 1, "应至少有一条历史版本")
        first_version = versions[0]
        self.assertIn("id", first_version)
        self.assertIn("content", first_version)
        self.assertIn("created_at", first_version)

        # 恢复为第一个版本（即 "first content"）
        version_id = first_version["id"]
        restore_resp = await self.client.post(
            f"/api/scenes/{self.scene_id}/restore_version",
            json={"version_id": version_id},
        )
        self.assertEqual(restore_resp.status_code, 200)
        restored = restore_resp.json()
        self.assertEqual(restored.get("content"), "first content")

        get_resp = await self.client.get(f"/api/scenes/{self.scene_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json().get("content"), "first content")


if __name__ == "__main__":
    unittest.main()
