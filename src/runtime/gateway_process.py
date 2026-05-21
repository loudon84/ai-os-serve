from __future__ import annotations

import asyncio
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path

from core.config import Settings
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GatewayProcessHandle:
    profile_id: str
    profile_name: str
    port: int
    pid: int | None = None
    process: asyncio.subprocess.Process | None = None
    log_path: Path | None = None
    _log_file: object | None = field(default=None, repr=False)

    def is_alive(self) -> bool:
        if self.process is None:
            return False
        return self.process.returncode is None


class GatewayProcessManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._handles: dict[str, GatewayProcessHandle] = {}

    def get_handle(self, profile_id: str) -> GatewayProcessHandle | None:
        return self._handles.get(profile_id)

    async def start(
        self,
        profile_id: str,
        profile_name: str,
        port: int,
        *,
        mock_command: list[str] | None = None,
    ) -> GatewayProcessHandle:
        if profile_id in self._handles and self._handles[profile_id].is_alive():
            return self._handles[profile_id]

        log_path = self._settings.log_dir_path / f"gateway-{profile_name}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = log_path.open("a", encoding="utf-8")

        if mock_command is not None:
            cmd = mock_command
        else:
            base = shlex.split(self._settings.hermes_gateway_command, posix=(sys.platform != "win32"))
            cmd = [*base, "--port", str(port), "--profile", profile_name]

        logger.info("gateway_starting", profile_id=profile_id, cmd=cmd, port=port)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=log_file,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(self._settings.hermes_home_path),
        )
        handle = GatewayProcessHandle(
            profile_id=profile_id,
            profile_name=profile_name,
            port=port,
            pid=process.pid,
            process=process,
            log_path=log_path,
            _log_file=log_file,
        )
        self._handles[profile_id] = handle
        return handle

    async def stop(self, profile_id: str) -> None:
        handle = self._handles.pop(profile_id, None)
        if handle is None:
            return
        if handle.process and handle.is_alive():
            handle.process.terminate()
            try:
                await asyncio.wait_for(handle.process.wait(), timeout=10.0)
            except TimeoutError:
                handle.process.kill()
                await handle.process.wait()
        if handle._log_file:
            handle._log_file.close()

    async def shutdown_all(self) -> None:
        for profile_id in list(self._handles.keys()):
            await self.stop(profile_id)

    def read_logs(self, profile_id: str, *, tail: int = 200) -> tuple[list[str], bool]:
        handle = self._handles.get(profile_id)
        if handle is None or handle.log_path is None or not handle.log_path.exists():
            # try log file by name from settings dir
            return [], False
        lines = handle.log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        truncated = len(lines) > tail
        return lines[-tail:], truncated
