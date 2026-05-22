from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_project_root() -> Path:
    """copilot-serve 仓库根目录（含 pyproject.toml）。"""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    # src/core/config.py -> copilot-serve
    return here.parents[2]


_PACKAGE_ROOT = _resolve_project_root()

# 与 smc-copilot-desktop 用户数据目录一致；可通过 SQLITE_PATH 覆盖
_DEFAULT_SQLITE_PATH = "~/.hermes/desktop/sqlite.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PACKAGE_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    copilot_host: str = Field(default="127.0.0.1", alias="COPILOT_HOST")
    copilot_port: int = Field(default=8765, alias="COPILOT_PORT")
    sqlite_path: str = Field(default=_DEFAULT_SQLITE_PATH, alias="SQLITE_PATH")
    hermes_home: str = Field(default="~/.hermes", alias="HERMES_HOME")
    default_gateway_port: int = Field(default=8642, alias="DEFAULT_GATEWAY_PORT")
    hermes_gateway_command: str = Field(default="hermes gateway", alias="HERMES_GATEWAY_COMMAND")
    log_dir: str = Field(default="./data/logs", alias="LOG_DIR")
    gateway_health_timeout_sec: float = Field(default=30.0, alias="GATEWAY_HEALTH_TIMEOUT_SEC")
    gateway_health_poll_interval_sec: float = Field(default=0.5, alias="GATEWAY_HEALTH_POLL_INTERVAL_SEC")

    # Team Task Hub (stub / HTTP placeholder)
    team_hub_base_url: str = Field(default="", alias="AIOS_TEAM_HUB_BASE_URL")
    team_hub_token: str = Field(default="", alias="AIOS_TEAM_HUB_TOKEN")
    device_id: str = Field(default="local-device", alias="AIOS_DEVICE_ID")
    agent_id: str = Field(default="hermes-local-agent", alias="AIOS_AGENT_ID")
    task_poll_interval_seconds: float = Field(default=10.0, alias="AIOS_TASK_POLL_INTERVAL_SECONDS")
    team_hub_use_stub: bool = Field(default=True, alias="AIOS_TEAM_HUB_USE_STUB")
    task_reject_sets_cancelled: bool = Field(default=False, alias="AIOS_TASK_REJECT_SETS_CANCELLED")

    # Workers
    run_event_poll_interval_seconds: float = Field(default=2.0, alias="AIOS_RUN_EVENT_POLL_INTERVAL_SECONDS")
    sync_outbox_interval_seconds: float = Field(default=5.0, alias="AIOS_SYNC_OUTBOX_INTERVAL_SECONDS")
    sync_outbox_max_retries: int = Field(default=20, alias="AIOS_SYNC_OUTBOX_MAX_RETRIES")

    task_routing_json: str = Field(
        default="",
        alias="TASK_ROUTING_JSON",
        description='Optional JSON: {"coding_task":{"profile_type":"coding","require_approval":true}}',
    )

    copilot_desktop_token: str = Field(default="", alias="COPILOT_DESKTOP_TOKEN")
    copilot_require_token: bool = Field(default=False, alias="COPILOT_REQUIRE_TOKEN")
    cors_allow_origins: str = Field(
        default="http://127.0.0.1,http://localhost",
        alias="CORS_ALLOW_ORIGINS",
        description="Comma-separated origins for copilot-desktop renderer",
    )

    @property
    def sqlite_url(self) -> str:
        path = Path(self.sqlite_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{path.as_posix()}"

    @property
    def hermes_home_path(self) -> Path:
        return Path(self.hermes_home).expanduser().resolve()

    @property
    def log_dir_path(self) -> Path:
        p = (_PACKAGE_ROOT / self.log_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def package_root(self) -> Path:
        return _PACKAGE_ROOT


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
