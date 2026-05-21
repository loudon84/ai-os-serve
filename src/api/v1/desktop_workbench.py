from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ai_copilot_serve.api.deps import get_app_settings, get_db_session, get_team_hub
from ai_copilot_serve.core.config import Settings
from ai_copilot_serve.integrations.team_hub.client import TeamHubClient
from ai_copilot_serve.schemas.v12_tasks import TaskWorkbenchSummary
from ai_copilot_serve.services.workbench_summary import build_task_workbench_summary

router = APIRouter(prefix="/desktop/task-workbench", tags=["desktop"])


@router.get("/summary", response_model=TaskWorkbenchSummary)
async def workbench_summary(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    hub: Annotated[TeamHubClient, Depends(get_team_hub)],
) -> TaskWorkbenchSummary:
    """DB aggregates plus Team Hub bookkeeping for the Electron workbench."""
    return await build_task_workbench_summary(session, settings, hub)
