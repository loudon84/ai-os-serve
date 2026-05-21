from __future__ import annotations

from typing import Any

from ai_copilot_serve.core.config import Settings
from ai_copilot_serve.integrations.hermes.profile_loader import load_profile_config, write_profile_config


def build_default_config(settings: Settings, name: str, gateway_port: int) -> dict[str, Any]:
    existing = load_profile_config(settings, name)
    gateway = existing.get("gateway", {}) if isinstance(existing.get("gateway"), dict) else {}
    gateway["port"] = gateway_port
    existing["gateway"] = gateway
    if "name" not in existing:
        existing["name"] = name
    return existing


def sync_profile_config(settings: Settings, name: str, gateway_port: int) -> str:
    config = build_default_config(settings, name, gateway_port)
    path = write_profile_config(settings, name, config)
    return str(path)
