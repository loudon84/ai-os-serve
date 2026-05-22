from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.deps import get_app_settings
from core.config import Settings
from local_service.service_state import build_service_status
from schemas.system import ServiceProfileCountsResponse, ServiceStatusResponse

router = APIRouter(prefix="/service", tags=["service"])


@router.get("/status", response_model=ServiceStatusResponse)
async def service_status(request: Request, settings: Settings = Depends(get_app_settings)) -> ServiceStatusResponse:
    session_maker = request.app.state.session_maker
    status = await build_service_status(settings, session_maker)
    return ServiceStatusResponse(
        service=status.service,
        version=status.version,
        pid=status.pid,
        uptime_seconds=status.uptime_seconds,
        host=status.host,
        port=status.port,
        sqlite_path=status.sqlite_path,
        hermes_home=status.hermes_home,
        profiles=ServiceProfileCountsResponse(
            total=status.profiles.total,
            running=status.profiles.running,
            error=status.profiles.error,
        ),
    )
