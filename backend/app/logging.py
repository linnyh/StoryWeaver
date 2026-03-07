"""Application logging helpers."""
import logging
from contextvars import ContextVar
from contextvars import Token

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Inject request id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_ctx.get()
        return True


def set_request_id(request_id: str) -> Token:
    """Bind request id to current context."""
    return _request_id_ctx.set(request_id)


def reset_request_id(token: Token) -> None:
    """Reset request id context."""
    _request_id_ctx.reset(token)


def get_request_id() -> str:
    """Get current request id from context."""
    return _request_id_ctx.get()

def setup_logging() -> None:
    """Configure base logging once for the process."""
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s [%(name)s] [req=%(request_id)s] %(message)s",
        )

    for handler in root_logger.handlers:
        has_filter = any(isinstance(f, RequestIdFilter) for f in handler.filters)
        if not has_filter:
            handler.addFilter(RequestIdFilter())


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger."""
    setup_logging()
    return logging.getLogger(name)
