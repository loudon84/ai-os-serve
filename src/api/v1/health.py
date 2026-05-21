from __future__ import annotations

from fastapi import APIRouter

from ai_copilot_serve import __version__
from ai_copilot_serve.schemas.system import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(version=__version__)
