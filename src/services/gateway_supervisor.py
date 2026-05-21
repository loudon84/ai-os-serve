from __future__ import annotations

import asyncio
import time

import psutil
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config import Settings
from core.constants import GatewayStatus
from core.errors import ConflictError, GatewayError
from core.logging import get_logger
from db.models.profile import Profile
from db.repositories.profile_repo import ProfileRepository
from integrations.hermes.client import HermesGatewayClient
from runtime.gateway_process import GatewayProcessManager
from schemas.profile import ProfileStatusResponse
from services.profile_service import ProfileService

logger = get_logger(__name__)


class GatewaySupervisor:
    def __init__(
        self,
        *,
        settings: Settings,
        session_maker: async_sessionmaker[AsyncSession],
        process_manager: GatewayProcessManager | None = None,
    ) -> None:
        self._settings = settings
        self._session_maker = session_maker
        self._process_manager = process_manager or GatewayProcessManager(settings)
        self._mock_command: list[str] | None = None

    def set_mock_gateway_command(self, cmd: list[str]) -> None:
        """Test hook: use mock HTTP gateway script instead of hermes CLI."""
        self._mock_command = cmd

    async def _with_session(self) -> tuple[AsyncSession, ProfileService]:
        session = self._session_maker()
        repo = ProfileRepository(session)
        return session, ProfileService(self._settings, repo)

    async def refresh_status(self, profile_id: str) -> ProfileStatusResponse:
        session, svc = await self._with_session()
        try:
            profile = await svc.get_profile(profile_id)
            return await self._compute_status(session, svc, profile)
        finally:
            await session.commit()
            await session.close()

    async def _compute_status(
        self, session: AsyncSession, svc: ProfileService, profile: Profile
    ) -> ProfileStatusResponse:
        handle = self._process_manager.get_handle(profile.id)
        alive = handle.is_alive() if handle else False
        pid = handle.pid if handle and alive else profile.gateway_pid

        if profile.status == GatewayStatus.RUNNING.value and not alive:
            if pid and not psutil.pid_exists(pid):
                profile = await svc.set_status(profile, GatewayStatus.ERROR)
                message = "Gateway process exited unexpectedly"
            else:
                message = "Gateway process not tracked locally"
                profile = await svc.set_status(profile, GatewayStatus.ERROR)
        elif alive and profile.status != GatewayStatus.RUNNING.value:
            profile = await svc.set_status(profile, GatewayStatus.RUNNING, pid=pid)
            message = None
        else:
            message = None

        healthy = False
        if profile.status == GatewayStatus.RUNNING.value:
            healthy = await HermesGatewayClient(profile.gateway_port).health_check()
            if not healthy and not alive:
                profile = await svc.set_status(profile, GatewayStatus.ERROR)
                message = "Gateway health check failed"

        await session.flush()
        return ProfileStatusResponse(
            profile_id=profile.id,
            status=GatewayStatus(profile.status),
            gateway_port=profile.gateway_port,
            gateway_pid=profile.gateway_pid,
            healthy=healthy,
            message=message,
        )

    async def start_profile(self, profile_id: str) -> ProfileStatusResponse:
        session, svc = await self._with_session()
        try:
            profile = await svc.get_profile(profile_id)
            if not profile.enabled:
                raise ConflictError(f"Profile {profile.name} is disabled")
            if profile.status in (GatewayStatus.STARTING.value, GatewayStatus.RUNNING.value):
                handle = self._process_manager.get_handle(profile.id)
                if handle and handle.is_alive():
                    return await self._compute_status(session, svc, profile)

            profile = await svc.set_status(profile, GatewayStatus.STARTING)
            await session.commit()

            await self._process_manager.start(
                profile.id,
                profile.name,
                profile.gateway_port,
                mock_command=self._mock_command,
            )
            handle = self._process_manager.get_handle(profile.id)
            profile = await svc.set_status(
                profile,
                GatewayStatus.RUNNING,
                pid=handle.pid if handle else None,
            )

            healthy = await self._wait_for_health(profile.gateway_port)
            if not healthy:
                profile = await svc.set_status(profile, GatewayStatus.ERROR)
                raise GatewayError(f"Gateway on port {profile.gateway_port} failed health check")

            await session.commit()
            return ProfileStatusResponse(
                profile_id=profile.id,
                status=GatewayStatus(profile.status),
                gateway_port=profile.gateway_port,
                gateway_pid=profile.gateway_pid,
                healthy=True,
                message=None,
            )
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def _wait_for_health(self, port: int) -> bool:
        client = HermesGatewayClient(port)
        deadline = time.monotonic() + self._settings.gateway_health_timeout_sec
        while time.monotonic() < deadline:
            if await client.health_check():
                return True
            await asyncio.sleep(self._settings.gateway_health_poll_interval_sec)
        return False

    async def stop_profile(self, profile_id: str) -> ProfileStatusResponse:
        session, svc = await self._with_session()
        try:
            profile = await svc.get_profile(profile_id)
            await self._process_manager.stop(profile.id)
            profile = await svc.set_status(profile, GatewayStatus.STOPPED)
            await session.commit()
            return ProfileStatusResponse(
                profile_id=profile.id,
                status=GatewayStatus.STOPPED,
                gateway_port=profile.gateway_port,
                gateway_pid=None,
                healthy=False,
                message=None,
            )
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def get_gateway_health(self, gateway_id: str) -> ProfileStatusResponse:
        # V1.0: gateway_id == profile_id
        return await self.refresh_status(gateway_id)

    def read_gateway_logs(self, gateway_id: str, *, tail: int = 200, profile_name: str | None = None) -> tuple[list[str], bool]:
        lines, truncated = self._process_manager.read_logs(gateway_id, tail=tail)
        if lines:
            return lines, truncated
        if profile_name:
            log_path = self._settings.log_dir_path / f"gateway-{profile_name}.log"
            if log_path.exists():
                all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
                truncated = len(all_lines) > tail
                return all_lines[-tail:], truncated
        return [], False

    async def shutdown_all(self) -> None:
        await self._process_manager.shutdown_all()

    async def get_profile_for_hermes(self, profile_id: str) -> Profile:
        session, svc = await self._with_session()
        try:
            profile = await svc.get_profile(profile_id)
            status = await self._compute_status(session, svc, profile)
            await session.commit()
            if status.status != GatewayStatus.RUNNING or not status.healthy:
                raise GatewayError(status.message or f"Gateway not ready: {status.status}")
            return profile
        finally:
            await session.close()
