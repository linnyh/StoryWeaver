import json
import unittest

from fastapi import HTTPException
from starlette.requests import Request

from app.errors import http_exception_handler, unhandled_exception_handler


def _make_request(path: str = "/test") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
    }
    request = Request(scope)
    request.state.request_id = "req-test-1"
    return request


class ErrorHandlersTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_exception_handler_includes_request_id(self):
        request = _make_request("/boom")
        response = await http_exception_handler(
            request,
            HTTPException(status_code=404, detail="not found"),
        )
        payload = json.loads(response.body)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(payload["request_id"], "req-test-1")
        self.assertEqual(payload["detail"], "not found")
        self.assertEqual(payload["error"]["type"], "http_error")

    async def test_unhandled_exception_handler_includes_request_id(self):
        request = _make_request("/fail")
        response = await unhandled_exception_handler(request, RuntimeError("x"))
        payload = json.loads(response.body)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(payload["request_id"], "req-test-1")
        self.assertEqual(payload["detail"], "Internal server error")
        self.assertEqual(payload["error"]["type"], "internal_error")


if __name__ == "__main__":
    unittest.main()
