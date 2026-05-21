from __future__ import annotations

from fastapi import APIRouter

from ai_copilot_serve.api.v1 import (
    approvals,
    desktop_workbench,
    gateways,
    health,
    hermes_runs,
    profiles,
    system,
    task_routing,
    tasks,
    team_tasks,
    workspaces,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(profiles.router)
api_router.include_router(gateways.router)
api_router.include_router(hermes_runs.router)
api_router.include_router(tasks.router)
api_router.include_router(team_tasks.router)
api_router.include_router(workspaces.router)
api_router.include_router(approvals.router)
api_router.include_router(task_routing.router)
api_router.include_router(desktop_workbench.router)
