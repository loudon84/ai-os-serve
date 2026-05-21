from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config import Settings, get_settings
from db.repositories.profile_repo import ProfileRepository
from db.repositories.role_spec_repo import RoleSpecRepository
from integrations.team_hub.client import TeamHubClient
from services.gateway_supervisor import GatewaySupervisor
from services.hermes_gateway_client import HermesGatewayService
from services.profile_service import ProfileService
from services.role_library_service import RoleLibraryService
from services.task_routing_registry import TaskRoutingRegistry
from services.task_runtime import TaskRuntimeService


def get_app_settings() -> Settings:
    return get_settings()


def get_session_maker(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_maker


def get_gateway_supervisor(request: Request) -> GatewaySupervisor:
    return request.app.state.gateway_supervisor


def get_team_hub(request: Request) -> TeamHubClient:
    return request.app.state.team_hub


def get_task_routing_registry(request: Request) -> TaskRoutingRegistry:
    return request.app.state.task_routing_registry


async def get_db_session(
    session_maker: async_sessionmaker[AsyncSession] = Depends(get_session_maker),
) -> AsyncIterator[AsyncSession]:
    session = session_maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_profile_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> ProfileService:
    return ProfileService(settings, ProfileRepository(session))


def get_role_library_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    supervisor: GatewaySupervisor = Depends(get_gateway_supervisor),
) -> RoleLibraryService:
    return RoleLibraryService(
        settings,
        ProfileRepository(session),
        RoleSpecRepository(session),
        gateway_supervisor=supervisor,
    )


def get_hermes_service() -> HermesGatewayService:
    return HermesGatewayService()


def get_task_runtime(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    gw: Annotated[GatewaySupervisor, Depends(get_gateway_supervisor)],
    rr: Annotated[TaskRoutingRegistry, Depends(get_task_routing_registry)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TaskRuntimeService:
    return TaskRuntimeService(db, settings, gw, rr)


def get_approval_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
):
    from services.approval_service import ApprovalService

    return ApprovalService(db, settings)


def verify_desktop_token(
    request: Request,
    settings: Annotated[Settings, Depends(get_app_settings)],
    token: Annotated[str | None, Header(alias="X-Copilot-Desktop-Token")] = None,
) -> None:
    if request.url.path in {"/api/v1/health", "/docs", "/openapi.json", "/redoc"}:
        return
    if not settings.copilot_require_token:
        return
    expected = settings.copilot_desktop_token
    if not expected:
        return
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing desktop token")
