from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from version import __version__
from api.middleware.cors_asgi import PureAsgiCorsMiddleware
from api.router import api_router
from core.config import get_settings
from core.errors import CopilotError
from core.lifecycle import lifespan
from schemas.common import ErrorResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title="smc-copilot-serve",
        version=__version__,
        description="smc-copilot-desktop local control plane",
        lifespan=lifespan,
    )

    @app.exception_handler(CopilotError)
    async def copilot_error_handler(_request: Request, exc: CopilotError) -> JSONResponse:
        code_map: dict[str, int] = {
            "not_found": 404,
            "conflict": 409,
            "gateway_error": 503,
            "hermes_client_error": 502,
            "policy_denied": 403,
            "invalid_state_transition": 409,
            "team_hub_error": 502,
        }
        status_code = code_map.get(exc.code, 400)
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(code=exc.code, message=exc.message).model_dump(),
        )

    app.include_router(api_router)
    return app


def build_asgi_app(fastapi_app: FastAPI | None = None) -> PureAsgiCorsMiddleware:
    """Wrap FastAPI with pure ASGI CORS (safe for SSE; used by uvicorn entry)."""
    inner = fastapi_app if fastapi_app is not None else create_app()
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    if not origins:
        origins = ["http://127.0.0.1", "http://localhost"]
    return PureAsgiCorsMiddleware(inner, allow_origins=origins)
