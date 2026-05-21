from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ai_copilot_serve.core.config import Settings, get_settings
from ai_copilot_serve.db.repositories.profile_repo import ProfileRepository
from ai_copilot_serve.integrations.team_hub.client import TeamHubClient
from ai_copilot_serve.services.gateway_supervisor import GatewaySupervisor
from ai_copilot_serve.services.hermes_gateway_client import HermesGatewayService
from ai_copilot_serve.services.profile_service import ProfileService
from ai_copilot_serve.services.task_routing_registry import TaskRoutingRegistry
from ai_copilot_serve.services.task_runtime import TaskRuntimeService


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
    from ai_copilot_serve.services.approval_service import ApprovalService

    return ApprovalService(db, settings)
