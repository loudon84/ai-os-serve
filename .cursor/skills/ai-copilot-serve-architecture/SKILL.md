---
name: smc-copilot-serve-architecture
description: Use when designing, refactoring, or reviewing smc-copilot-serve architecture, module boundaries, service layout, API contracts, or database model placement for the local Hermes control plane.
license: Proprietary
compatibility: Designed for Cursor Agent, Python 3.12, FastAPI, SQLAlchemy, SQLite, Hermes Gateway integration.
metadata:
  version: "1.0"
  owner: "smc-copilot-desktop"
---

# smc-copilot-serve Architecture Skill

## When to activate

Use this skill when the user asks for architecture, project structure, module design, API layout, refactor strategy, or implementation planning for `smc-copilot-serve`.

## System boundary

`smc-copilot-serve` is the local service layer for `smc-copilot-desktop`.

It must coordinate:

- HermesLocalService local control plane
- multiple Hermes Gateway profiles
- Profile Runtime
- Gateway Supervisor
- Team Task Runtime
- Approval Runtime
- Workspace Guard
- Audit Log
- Windows service packaging

## Architecture rules

1. Keep the service local-first. Use SQLite first. Do not introduce Postgres, Redis, MQ, or Kubernetes unless the task explicitly requires it.
2. Treat Hermes Gateway as an external runtime. Never embed Hermes internals directly into API routers.
3. Keep process management under `runtime/` and `services/gateway_supervisor.py`.
4. Keep remote collaboration under `integrations/team_hub/` and `services/task_runtime.py`.
5. Keep risky local operations behind `workspace_guard.py` and `approval_service.py`.
6. Every new runtime state must be persisted if the desktop must recover after restart.
7. Every background loop must be cancellable and lifecycle-managed.

## Preferred module mapping

```text
src/ai_copilot_serve/
  api/v1/               # FastAPI routes
  schemas/              # Pydantic DTOs
  db/models/            # SQLAlchemy models
  db/repositories/      # DB access
  services/             # business orchestration
  integrations/hermes/  # Hermes Gateway clients and config
  integrations/team_hub/# remote task hub clients
  integrations/local_shell/# command execution adapters
  runtime/              # process registry and runtime state
  workers/              # background loops
```

## Design output format

When producing architecture output, always include:

1. Target module
2. Responsibility
3. Files to create or modify
4. API contract impact
5. DB migration impact
6. Test plan
7. Windows compatibility impact
8. Security impact

## Rejection criteria

Reject or redesign plans that:

- put Hermes Gateway process control inside Electron Renderer
- let React UI execute shell commands
- bypass approval for dangerous operations
- hardcode profile ports without collision checks
- mix database logic into routers
- store secrets in SQLite without encryption or redaction strategy
