"""Global exception handlers."""
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.logging import get_logger, get_request_id

logger = get_logger(__name__)


def _resolve_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or get_request_id()


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Normalize HTTP error responses."""
    request_id = _resolve_request_id(request)
    logger.warning(
        "HTTP error status=%s path=%s req=%s detail=%s",
        exc.status_code,
        request.url.path,
        request_id,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "request_id": request_id,
            "detail": exc.detail,
            "error": {
                "type": "http_error",
                "message": exc.detail,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Normalize request validation errors."""
    request_id = _resolve_request_id(request)
    logger.warning(
        "Validation error path=%s req=%s errors=%s",
        request.url.path,
        request_id,
        exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "request_id": request_id,
            "detail": "Request validation failed",
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unexpected errors and return a stable payload."""
    request_id = _resolve_request_id(request)
    logger.exception("Unhandled error path=%s req=%s", request.url.path, request_id)
    return JSONResponse(
        status_code=500,
        content={
            "request_id": request_id,
            "detail": "Internal server error",
            "error": {
                "type": "internal_error",
                "message": "Internal server error",
            }
        },
    )
