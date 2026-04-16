from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.responses import Response


async def handle_unexpected_exception(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Convert unexpected request errors to logged HTTP 500 responses."""
    try:
        return await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled exception during request processing: {} {}",
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handling middleware."""
    app.middleware("http")(handle_unexpected_exception)
