# Backend Testing Guide

This project currently uses Python `unittest` for backend tests.

## Test Types

- Unit tests: cover usecases, postprocess services, and error handlers.
- Integration tests: run HTTP-level API flow against FastAPI ASGI app.

## Test Files

- `test_scene_image_service.py`
- `test_errors_unittest.py`
- `test_scene_usecases_unittest.py`
- `test_scene_postprocess_unittest.py`
- `test_chapter_usecases_unittest.py`
- `test_novel_usecases_unittest.py`
- `test_api_integration_unittest.py`

## Run Tests Locally

From `backend/`:

```bash
python -m unittest -q \
  test_scene_image_service.py \
  test_errors_unittest.py \
  test_scene_usecases_unittest.py \
  test_scene_postprocess_unittest.py \
  test_chapter_usecases_unittest.py \
  test_novel_usecases_unittest.py \
  test_api_integration_unittest.py
```

Run a single file:

```bash
python -m unittest -q test_api_integration_unittest.py
```

## What Integration Test Covers

- `GET /health` basic liveness.
- Global error payload format (`request_id`, `error.type`) for 404.
- Novel core CRUD path: create, get, update, list, delete.
- `X-Request-ID` response propagation.

## CI

GitHub Actions workflow:

- `.github/workflows/backend-ci.yml`

It runs on `push` / `pull_request` when backend files change and executes the same test command above.

## Notes

- Integration tests initialize the database with `init_db()`.
- Local test runs may create SQLite WAL helper files (`storyweaver.db-wal`, `storyweaver.db-shm`); these should not be committed.
