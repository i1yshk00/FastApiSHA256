from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.v1.router import api_router
from app.core.config import loguru_config_obj, settings
from app.core.exceptions import register_exception_handlers

loguru_config_obj.setup_logging()

PROJECT_DESCRIPTION = """
Async REST API for a backend test assignment.

The service allows users to authenticate, retrieve their profile, view their
accounts, and inspect their transactions. Administrators can manage users and
retrieve users with their account balances. External transaction webhooks are
validated with a SHA256 signature before updating account balances.
"""

app = FastAPI(
    title=settings.APP_NAME,
    description=PROJECT_DESCRIPTION,
    debug=settings.DEBUG,
)
register_exception_handlers(app)
app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect the service root to the generated OpenAPI documentation."""
    return RedirectResponse(url="/docs")


@app.get("/healthcheck", tags=["Base URLs"])
async def healthcheck() -> dict[str, str]:
    """Return a lightweight health response for service availability checks."""
    return {"message": "Healthy"}
