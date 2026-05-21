from __future__ import annotations

from typing import Any

from core.constants import GatewayStatus
from core.errors import GatewayError
from db.models.profile import Profile
from integrations.hermes.client import HermesGatewayClient, extract_run_id
from schemas.hermes import HermesRunCreate


class HermesGatewayService:
    def _client(self, profile: Profile) -> HermesGatewayClient:
        if profile.status != GatewayStatus.RUNNING.value:
            raise GatewayError(f"Profile {profile.name} gateway is not running (status={profile.status})")
        return HermesGatewayClient(profile.gateway_port)

    async def list_models(self, profile: Profile) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        return await self._client(profile).list_models()

    async def create_run(self, profile: Profile, body: HermesRunCreate) -> tuple[str, dict[str, Any]]:
        data = await self._client(profile).create_run(
            model=body.model,
            input_payload=body.input,
            metadata=body.metadata,
        )
        return extract_run_id(data), data

    async def get_run(self, profile: Profile, run_id: str) -> dict[str, Any]:
        return await self._client(profile).get_run(run_id)

    async def list_run_events(self, profile: Profile, run_id: str) -> list[dict[str, Any]]:
        return await self._client(profile).list_run_events(run_id)
