from __future__ import annotations

from enum import StrEnum


class ProfileType(StrEnum):
    DEFAULT = "default"
    WRITER = "writer"
    CODING = "coding"
    FINANCE = "finance"
    RESEARCH = "research"


class GatewayStatus(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    RESTARTING = "restarting"
