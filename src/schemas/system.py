from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "ai-copilot-serve"
    version: str = "0.1.0"


class SystemInfoResponse(BaseModel):
    service: str
    version: str
    hermes_home: str
    sqlite_path: str
    default_gateway_port: int
