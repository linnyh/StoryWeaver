import unittest
import uuid

import httpx

from app.database import init_db
from app.main import app


class ApiIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()
        transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_health_endpoint(self):
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "healthy")
        self.assertIn("X-Request-ID", response.headers)

    async def test_not_found_error_payload_shape(self):
        response = await self.client.get("/api/novels/not-exist")
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertIn("request_id", body)
        self.assertIn("error", body)
        self.assertEqual(body["error"].get("type"), "http_error")
        self.assertIn("X-Request-ID", response.headers)

    async def test_novel_crud_flow(self):
        request_id = str(uuid.uuid4())
        create_payload = {
            "title": f"integration-{request_id[:8]}",
            "premise": "integration test",
            "genre": "玄幻",
            "tone": "严肃",
        }

        create_resp = await self.client.post(
            "/api/novels/",
            json=create_payload,
            headers={"X-Request-ID": request_id},
        )
        self.assertEqual(create_resp.status_code, 200)
        self.assertEqual(create_resp.headers.get("X-Request-ID"), request_id)

        created = create_resp.json()
        novel_id = created["id"]

        get_resp = await self.client.get(f"/api/novels/{novel_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json().get("id"), novel_id)

        update_resp = await self.client.put(
            f"/api/novels/{novel_id}",
            json={"tone": "黑暗"},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json().get("tone"), "黑暗")

        list_resp = await self.client.get("/api/novels/")
        self.assertEqual(list_resp.status_code, 200)
        ids = {item["id"] for item in list_resp.json()}
        self.assertIn(novel_id, ids)

        delete_resp = await self.client.delete(f"/api/novels/{novel_id}")
        self.assertEqual(delete_resp.status_code, 200)
        self.assertEqual(delete_resp.json().get("message"), "Novel deleted")


if __name__ == "__main__":
    unittest.main()
