# smc-copilot-serve API Contract (V1.0)

Base URL: `http://127.0.0.1:8765` (configurable via `COPILOT_HOST` / `COPILOT_PORT`)

> **代码根目录**: 扁平 `src/`（`api/v1/`、`services/`、`db/models/`、`schemas/`）。启动：`uvicorn main:app`。SQLite 默认 `~/.hermes/desktop/sqlite.db`；建表仅用 Alembic。

## System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Service liveness |
| GET | `/api/v1/system/info` | Version, paths, default gateway port |

## Profiles

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/profiles` | List profiles |
| POST | `/api/v1/profiles` | Create profile |
| GET | `/api/v1/profiles/{profile_id}` | Get profile |
| PATCH | `/api/v1/profiles/{profile_id}` | Update profile |
| DELETE | `/api/v1/profiles/{profile_id}` | Delete profile |
| POST | `/api/v1/profiles/{profile_id}/start` | Start gateway |
| POST | `/api/v1/profiles/{profile_id}/stop` | Stop gateway |
| GET | `/api/v1/profiles/{profile_id}/status` | Profile + gateway status |

### ProfileCreate

```json
{
  "name": "default",
  "type": "default",
  "gateway_port": 8642,
  "enabled": true,
  "auto_start": false
}
```

### ProfileStatusResponse

```json
{
  "profile_id": "uuid",
  "status": "running",
  "gateway_port": 8642,
  "gateway_pid": 12345,
  "healthy": true,
  "message": null
}
```

Status values: `stopped`, `starting`, `running`, `error`, `restarting`.

## Gateways (V1.0: gateway_id = profile_id)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/gateways/{gateway_id}/health` | Gateway health |
| GET | `/api/v1/gateways/{gateway_id}/logs?tail=200` | Tail gateway stdout log |

## Hermes proxy

Requires profile gateway `running` and `healthy`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/profiles/{profile_id}/models` | Proxy `GET /v1/models` |
| POST | `/api/v1/profiles/{profile_id}/runs` | Proxy `POST /v1/runs` |
| GET | `/api/v1/profiles/{profile_id}/runs/{run_id}` | Proxy `GET /v1/runs/{id}` |
| GET | `/api/v1/profiles/{profile_id}/runs/{run_id}/events` | Proxy run events |

### HermesRunCreate

```json
{
  "model": "optional-model-id",
  "input": "prompt text or structured object",
  "metadata": {}
}
```

## Errors

JSON body:

```json
{
  "code": "not_found",
  "message": "Profile xyz not found"
}
```

| code | HTTP |
|------|------|
| not_found | 404 |
| conflict | 409 |
| gateway_error | 503 |
| hermes_client_error | 502 |
| policy_denied | 403 |
| invalid_state_transition | 409 |
| team_hub_error | 502 |

## V1.2 — Local tasks, Team Hub stub, approvals, workspaces, sync outbox

Environment variables: see repository `.env.example` (`AIOS_*`, `TASK_ROUTING_JSON`).

### Copilot ↔ Team Hub (placeholder)

The service uses a **port-style** `TeamHubClient` (`poll_assignments`, `claim_assignment`, `push_task_update`). Default is `StubTeamHubClient`; set `AIOS_TEAM_HUB_BASE_URL` and `AIOS_TEAM_HUB_USE_STUB=false` to use `HttpTeamHubClient` against a real hub when paths are finalized.

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tasks` | List local tasks |
| POST | `/api/v1/tasks` | Create local task |
| GET | `/api/v1/tasks/{task_id}` | Get task |
| POST | `/api/v1/tasks/{task_id}/run` | Execute Hermes run (gateway must be running + healthy) |
| POST | `/api/v1/tasks/{task_id}/cancel` | Cancel task / best-effort Hermes cancel |
| POST | `/api/v1/tasks/{task_id}/bind-profile` | JSON body `{ "profile_id": "..." }` |
| GET | `/api/v1/tasks/{task_id}/events` | Task event log |
| GET | `/api/v1/tasks/{task_id}/events/stream` | SSE-style stream (polling backend) |
| POST | `/api/v1/tasks/{task_id}/request-approval` | Query: `action_type`, optional `risk_level`, `requested_by` |

### Team task bindings

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/team-tasks/pull` | Poll Hub (stub clears queue), ingest + claim |
| GET | `/api/v1/team-tasks` | List bindings |
| GET | `/api/v1/team-tasks/{binding_id}` | Get binding |
| POST | `/api/v1/team-tasks/{binding_id}/claim` | Re-claim on Hub |
| POST | `/api/v1/team-tasks/{binding_id}/sync` | Enqueue outbox sync for bound local task |

### Task routing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/task-routing` | Effective rules (defaults + env + PATCH) |
| PATCH | `/api/v1/task-routing` | Body `{ "rules": { "<task_type>": { "profile_type": "...", "require_approval": bool } } }` |

### Approvals

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/approvals` | Recent approvals |
| GET | `/api/v1/approvals/pending` | Pending only |
| GET | `/api/v1/approvals/{id}` | Get one |
| POST | `/api/v1/approvals/{id}/approve` | Optional JSON `{ "approved_by": "..." }` |
| POST | `/api/v1/approvals/{id}/reject` | Optional JSON `{ "actor": "...", "reason": "..." }` |

### Workspaces

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/workspaces` | List |
| POST | `/api/v1/workspaces` | Create |
| GET | `/api/v1/workspaces/{id}` | Get |
| PATCH | `/api/v1/workspaces/{id}` | Update |
| DELETE | `/api/v1/workspaces/{id}` | Delete |
| POST | `/api/v1/workspaces/{id}/validate-path` | Body `{ "path": "..." }` |
| POST | `/api/v1/workspaces/{id}/validate-command` | Body `{ "command": "..." }` returns `classification` |

### Desktop workbench

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/desktop/task-workbench/summary` | Counts: profiles / tasks / approvals by status + stub Hub counters |
| GET | `/api/v1/desktop/task-workbench/events/stream` | **SSE** global workbench events: `task_created` / `task_updated` / `approval_created` / `ping` (10s); supports `Last-Event-ID` |

Task timeline SSE (`GET /api/v1/tasks/{task_id}/events/stream`): `text/event-stream` with full `event_payload`, `run_id`, `Last-Event-ID`, idle `ping`, and stream closes **30s** after task reaches `completed` / `failed` / `cancelled`.

### Desktop auth (optional)

When `COPILOT_REQUIRE_TOKEN=true`, send header `X-Copilot-Desktop-Token: <COPILOT_DESKTOP_TOKEN>` on all `/api/v1/*` except `/api/v1/health`. Electron Main injects the token when spawning uvicorn; Renderer reads it via `window.copilotServe.getConnection()`.

CORS: SSE responses include `Access-Control-Allow-Origin: http://127.0.0.1` for local Portal/Desktop fetch.

## team_v1.7 — Windows Desktop 部署

| 组件 | 说明 |
|------|------|
| 安装根目录 | `%LOCALAPPDATA%\Programs\SMC Copilot\runtime\copilot-serve` |
| 部署脚本 | `runtime\deploy-copilot-serve.ps1`（clone、venv、`uv sync --extra service`、`.env`、`alembic upgrade head`） |
| 环境变量 | `COPILOT_SERVE_ROOT`、`COPILOT_SERVE_PYTHON`（`.venv\Scripts\python.exe`）、`COPILOT_SERVE_PORT`（默认 8765） |
| 启动方式 | **默认**：copilot-desktop Main Process `spawn` uvicorn；**可选**：`ai-copilot-service` Windows Service（勿与 spawn 同端口） |
| SQLite | `~/.hermes/desktop/sqlite.db`（与 Desktop 一致） |
| 验收 | `scripts/smoke-test-windows.ps1` 对运行中实例执行 health / profiles / 可选 gateway start |

Desktop Renderer 通过 `window.copilotServe` 获取 connection（含 token）、状态、日志，并可触发 deploy / precheck。

## V1.0 acceptance checklist

1. `GET /api/v1/profiles` lists registered profiles.
2. `POST /api/v1/profiles/{id}/start` → `status=running`, `healthy=true`.
3. `GET /api/v1/profiles/{id}/models` returns models from gateway.
4. `POST /api/v1/profiles/{id}/runs` returns `run_id`; events endpoint works.
5. After gateway process kill, `GET .../status` reports `error` or `stopped`, `healthy=false`.
