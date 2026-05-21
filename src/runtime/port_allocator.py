from __future__ import annotations

from core.config import Settings


def allocate_port(settings: Settings, requested: int | None) -> int:
    if requested is not None:
        return requested
    return settings.default_gateway_port
