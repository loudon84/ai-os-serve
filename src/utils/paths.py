from __future__ import annotations

from pathlib import Path

from core.config import Settings


def profile_dir(settings: Settings, name: str) -> Path:
    return settings.hermes_home_path / "profiles" / name


def profile_config_path(settings: Settings, name: str) -> Path:
    return profile_dir(settings, name) / "config.yaml"
