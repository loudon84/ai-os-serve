# AGENTS.md

## Project identity

This repository implements `ai-copilot-serve`, the local control-plane service for `ai-os-desktop`.

The service is not a generic backend. It manages local Hermes Agent runtimes, multiple Hermes Gateway profiles, team-assigned tasks, approval gates, workspace safety policies, and the API surface consumed by Electron / React desktop UI.

Primary architecture path:

```text
Electron Desktop UI
  -> ai-copilot-serve / HermesLocalService
  -> Hermes Gateway Profiles
  -> Team Task Hub / Workspace / Local Tools
```

## Non-negotiable boundaries

1. Electron Renderer must not directly manage Hermes processes.
2. Electron Renderer must not read or write `~/.hermes` directly.
3. Electron Renderer must not execute shell commands directly.
4. All local runtime actions must go through `ai-copilot-serve` APIs.
5. All Hermes Gateway access must go through `HermesGatewayClient` or an adapter under `integrations/hermes/`.
6. All risky actions must go through Approval Runtime and Workspace Guard.
7. Never hardcode user secrets, model API keys, workspace paths, or private Git URLs.
8. Do not change public API contracts without updating schemas, tests, and docs.

## Target stack

Backend:

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic v2 and pydantic-settings
- SQLAlchemy 2.x
- Alembic
- SQLite for local-first desktop state
- httpx for outbound HTTP
- asyncio subprocess and psutil for process supervision
- pytest and pytest-asyncio

Desktop integration:

- Electron Main Process talks to `ai-copilot-serve` over local HTTP.
- Renderer talks to Main Process or local API through a typed client.
- Preload API must expose only a minimal whitelist.

## Expected repository layout

```text
src/                                    # 主代码根目录 (包名 ai_copilot_serve)
  __init__.py
  main.py                               # 入口: ai_copilot_serve.main:app
  app.py                                 # FastAPI 应用工厂
  core/
    config.py
    constants.py
    enums.py
    errors.py
    lifecycle.py
    logging.py
    task_routing.py
  api/
    deps.py
    router.py
    v1/
      health.py
      system.py
      profiles.py
      gateways.py
      hermes_runs.py
      tasks.py
      team_tasks.py
      task_routing.py
      approvals.py
      workspaces.py
      desktop_workbench.py
  db/
    base.py
    session.py
    models/
      __init__.py
      profile.py
      local_task.py
      task_related.py
      workspace_db.py
    repositories/
      profile_repo.py
      v12_repos.py
  schemas/
    common.py
    profile.py
    gateway.py
    hermes.py
    system.py
    v12_tasks.py
  services/
    profile_service.py
    gateway_supervisor.py
    hermes_gateway_client.py
    task_runtime.py
    task_state_machine.py
    task_sync_service.py
    task_routing_registry.py
    approval_service.py
    workspace_guard.py
    workbench_summary.py
  integrations/
    hermes/
      client.py
      config_writer.py
      profile_loader.py
    team_hub/
      client.py
      dto.py
      errors.py
  runtime/
    gateway_process.py
    port_allocator.py
  workers/
    v12_workers.py
  utils/
    paths.py

migrations/
tests/
docs/
scripts/
prd/
```

## Module responsibilities

### `core/`

Cross-cutting configuration, logging, lifecycle, error handling, and security helpers.

### `api/v1/`

FastAPI routers only. Routers must stay thin. Do not put business logic in routers.

### `schemas/`

Pydantic request and response models. Use explicit DTOs. Do not return ORM models directly.

### `db/models/`

SQLAlchemy models only.

### `db/repositories/`

Database access layer. Repositories must not call Hermes Gateway, shell, filesystem mutations, or remote Team Hub APIs.

### `services/`

Business orchestration layer.

### `integrations/hermes/`

Hermes profile loading, config generation, gateway HTTP client, run event streaming.

### `integrations/team_hub/`

Remote task hub client and sync logic.

### `integrations/local_shell/` (规划中)

Command runner and command policy. Shell execution must be mediated by Workspace Guard and Approval Runtime. 当前 Workspace Guard 实现在 `services/workspace_guard.py`，local_shell 集成待实现。

### `runtime/`

Profile runtime state, gateway process registry, port allocation, heartbeat, and locks.

### `workers/`

Background polling, gateway health checks, retry, and cleanup.

## Development commands

Prefer `uv` if the repository uses it. Otherwise use the checked-in project manager.

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn ai_copilot_serve.main:app --reload --host 127.0.0.1 --port 8765
uv run pytest
uv run ruff check .
uv run mypy src
```

If the project uses PowerShell scripts on Windows, prefer:

```powershell
scripts/smoke-test.ps1
```

Do not invent commands. Inspect `pyproject.toml`, `README.md`, and `scripts/` before running anything.

## Coding rules

1. Use typed Python. Add type hints for public functions.
2. Use async for HTTP clients, stream handling, and process orchestration where appropriate.
3. Avoid global mutable runtime state. Use registries and lifecycle-managed dependencies.
4. All API responses must use Pydantic schemas.
5. All DB schema changes require Alembic migration.
6. Every service change should include unit tests or integration tests.
7. Long-running loops must support cancellation.
8. Process supervision must handle start, stop, restart, crash detection, and log capture.
9. Use explicit status enums for profile, gateway, task, approval, and run state.
10. Keep Windows 10 Home compatibility in mind.

## Safety rules

Before implementing anything that executes commands, modifies files, changes Git state, or deploys containers:

1. Validate workspace policy.
2. Check command allowlist / denylist.
3. Determine whether approval is required.
4. Record audit log.
5. Make execution idempotent when possible.
6. Return structured errors.

Never bypass `WorkspaceGuard` or `ApprovalService` for:

- shell command execution
- file write outside allowed workspace paths
- `git commit`, `git push`, `git reset`, `git clean`
- Docker start / stop / compose operations
- Hermes profile config mutation
- remote task attachment download

## API design rules

Use these route groups:

```text
/api/v1/health
/api/v1/system
/api/v1/profiles
/api/v1/gateways
/api/v1/profiles/{profile_id}/models
/api/v1/profiles/{profile_id}/runs
/api/v1/tasks
/api/v1/approvals
/api/v1/workspaces
/api/v1/audit
```

Rules:

1. Keep route naming stable.
2. Return structured errors with machine-readable codes.
3. Do not leak local filesystem secrets in error responses.
4. Use pagination for list endpoints that can grow.
5. Stream Hermes run events through SSE-compatible endpoints.

## Hermes integration rules

Hermes Gateway behavior must be isolated behind `HermesGatewayClient`.

Required client methods:

```python
list_models(profile_id: str) -> list[HermesModel]
create_run(profile_id: str, request: CreateRunRequest) -> HermesRun
stream_run_events(profile_id: str, run_id: str) -> AsyncIterator[HermesRunEvent]
get_run(profile_id: str, run_id: str) -> HermesRun
cancel_run(profile_id: str, run_id: str) -> None
```

Never call Hermes Gateway URLs directly from API routers.

## Gateway Supervisor rules

Gateway lifecycle must support:

```text
STOPPED -> STARTING -> RUNNING -> ERROR -> RESTARTING -> RUNNING
```

Implementation requirements:

1. Each profile must have a stable gateway port.
2. Default profile should normally use `8642` unless configured otherwise.
3. Additional profiles must use allocated ports and must not collide.
4. A crashed profile must not terminate other profiles.
5. Logs must be separated by profile.
6. Health checks must not block the API event loop.

## Team Task Runtime rules

Remote task sync should start with polling. Do not introduce message queues unless explicitly required.

Task state model:

```text
REMOTE_ASSIGNED
LOCAL_CREATED
WAITING_APPROVAL
APPROVED
RUNNING
NEED_HUMAN_INPUT
COMPLETED
FAILED
CANCELLED
SYNCED
```

Rules:

1. Use `remote_task_id + assignment_id + local_attempt_id` for idempotency.
2. Claim before execution.
3. Bind each task to a target profile.
4. Persist all state transitions.
5. Sync results back to Team Task Hub.
6. Failed sync must be retryable.

## Testing requirements

For any non-trivial change, add or update tests.

Minimum test coverage by module:

- Profile Runtime: profile CRUD, config path handling, port allocation.
- Gateway Supervisor: start/stop/restart state transitions with mocked subprocess.
- Hermes Client: models, runs, stream events with mocked HTTP.
- Task Runtime: polling, claim, local creation, idempotency, sync.
- Approval Runtime: pending/approve/reject flows.
- Workspace Guard: allowlist, denylist, path traversal, command policy.

Before finalizing a change, run the smallest relevant test set first, then broader tests if time allows.

## Documentation rules

Update docs when changing architecture, API contracts, runtime behavior, or deployment scripts.

Expected docs:

```text
docs/INDEX.md
docs/api-contract.md
```

## Pull request / change summary format

Every completed agent task should produce:

```text
Summary:
- What changed
- Why it changed
- Main files touched

Validation:
- Commands run
- Tests passed / failed
- Manual checks

Risk:
- Runtime impact
- Migration impact
- Windows impact
- Security impact

Follow-ups:
- Remaining work
```

## When uncertain

Do not guess external API contracts, Hermes CLI flags, Windows service details, or database schema.

Instead:

1. Inspect existing code and docs.
2. Search repository references.
3. Add a small adapter interface if the implementation detail is unstable.
4. Keep behavior behind tests.
