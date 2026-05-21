from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ai_copilot_serve import __version__
from ai_copilot_serve.api.router import api_router
from ai_copilot_serve.core.errors import CopilotError
from ai_copilot_serve.core.lifecycle import lifespan
from ai_copilot_serve.schemas.common import ErrorResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title="ai-copilot-serve",
        version=__version__,
        description="ai-os-desktop local control plane",
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
