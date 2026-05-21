from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_copilot_serve.core.config import get_settings
from ai_copilot_serve.core.logging import configure_logging, get_logger
from ai_copilot_serve.db.session import create_engine, create_sessionmaker, init_db
from ai_copilot_serve.integrations.team_hub.client import HttpTeamHubClient, StubTeamHubClient
from ai_copilot_serve.services.gateway_supervisor import GatewaySupervisor
from ai_copilot_serve.services.task_routing_registry import TaskRoutingRegistry
from ai_copilot_serve.workers.v12_workers import RunEventWorker, SyncOutboxWorker, TaskListenerWorker

logger = get_logger(__name__)


def _hub_factory(settings) -> StubTeamHubClient | HttpTeamHubClient:
    if settings.team_hub_use_stub or not (settings.team_hub_base_url or "").strip():
        return StubTeamHubClient()
    return HttpTeamHubClient(
        settings.team_hub_base_url,
        settings.team_hub_token or "",
        settings.device_id,
        settings.agent_id,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings = get_settings()

    injected_engine = getattr(app.state, "_test_engine", None)
    if injected_engine is not None:
        engine = injected_engine
        await init_db(engine)
    else:
        engine = create_engine(settings)
        await init_db(engine)

    session_maker = create_sessionmaker(engine)

    injected_supervisor = getattr(app.state, "_test_gateway_supervisor", None)
    if injected_supervisor is not None:
        supervisor = injected_supervisor
    else:
        supervisor = GatewaySupervisor(settings=settings, session_maker=session_maker)

    registry = getattr(app.state, "_test_task_routing_registry", None) or TaskRoutingRegistry(settings)

    injected_hub = getattr(app.state, "_test_team_hub", None)
    hub = injected_hub if injected_hub is not None else _hub_factory(settings)

    app.state.engine = engine
    app.state.session_maker = session_maker
    app.state.gateway_supervisor = supervisor
    app.state.team_hub = hub
    app.state.task_routing_registry = registry

    bg_tasks: list[asyncio.Task[None]] = []
    disable_workers = bool(getattr(app.state, "_disable_workers", False))

    if not disable_workers:
        listener = TaskListenerWorker(
            settings=settings, session_maker=session_maker, supervisor=supervisor, hub=hub, routing=registry
        )
        syncer = SyncOutboxWorker(settings=settings, session_maker=session_maker, hub=hub)
        run_ev = RunEventWorker(settings=settings, session_maker=session_maker)
        bg_tasks = [
            asyncio.create_task(listener.run_forever()),
            asyncio.create_task(syncer.run_forever()),
            asyncio.create_task(run_ev.run_forever()),
        ]

    logger.info(
        "ai_copilot_serve_started",
        host=settings.copilot_host,
        port=settings.copilot_port,
        workers=not disable_workers,
    )

    yield

    for t in bg_tasks:
        t.cancel()
    if bg_tasks:
        await asyncio.gather(*bg_tasks, return_exceptions=True)

    await supervisor.shutdown_all()
    await engine.dispose()
    logger.info("ai_copilot_serve_stopped")
