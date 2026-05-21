from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

# src layout: ensure package importable before editable install
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ai_copilot_serve.app import create_app
from ai_copilot_serve.core.config import Settings, get_settings
from ai_copilot_serve.core.lifecycle import lifespan
from ai_copilot_serve.db.session import create_engine, create_sessionmaker
from ai_copilot_serve.integrations.team_hub.client import StubTeamHubClient
from ai_copilot_serve.runtime.gateway_process import GatewayProcessManager
from ai_copilot_serve.services.gateway_supervisor import GatewaySupervisor


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    return data


@pytest.fixture
def test_settings(tmp_data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    db_path = tmp_data_dir / "test.db"
    log_dir = tmp_data_dir / "logs"
    hermes_home = tmp_data_dir / "hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("DEFAULT_GATEWAY_PORT", "18742")
    import ai_copilot_serve.core.config as config_mod

    config_mod._settings = None
    return get_settings()


@pytest_asyncio.fixture
async def app_client(
    test_settings: Settings,
) -> AsyncIterator[tuple[AsyncClient, GatewaySupervisor, Settings, StubTeamHubClient]]:
    engine: AsyncEngine = create_engine(test_settings)
    session_maker = create_sessionmaker(engine)
    process_manager = GatewayProcessManager(test_settings)
    supervisor = GatewaySupervisor(
        settings=test_settings,
        session_maker=session_maker,
        process_manager=process_manager,
    )
    stub_hub = StubTeamHubClient()

    app = create_app()
    app.state._test_engine = engine
    app.state._test_gateway_supervisor = supervisor
    app.state._test_team_hub = stub_hub
    app.state._disable_workers = True

    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, supervisor, test_settings, stub_hub

    import ai_copilot_serve.core.config as config_mod

    config_mod._settings = None
