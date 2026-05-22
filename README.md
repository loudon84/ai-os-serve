# smc-copilot-serve

smc-copilot-desktop 本地控制面：Hermes Profile、Gateway 启停、models/runs 代理。

## 开发

代码布局：扁平 `src/`（`PYTHONPATH=src` 或 `pip install -e` 后 `from core`、`from api` 等）。

```bash
cd copilot-serve
cp .env.example .env
pip install -e ".[dev]"
alembic upgrade head
uvicorn main:app --app-dir src --reload --host 127.0.0.1 --port 8765
```

### SQLite

| 场景 | `SQLITE_PATH` |
|------|----------------|
| 默认（未设置 / `.env.example`） | `~/.hermes/desktop/sqlite.db` |
| 仅仓库内调试（可选） | `./data/sqlite.db`（需在 `copilot-serve/` 下启动） |
| Electron 集成 | Main spawn 注入 `~/.hermes/desktop/sqlite.db` 或绝对路径 |

**建表**：生产/开发启动前执行 `alembic upgrade head`；应用启动时不再 `create_all`。

## 迁移

```bash
alembic upgrade head
```

## 测试

```bash
pytest
```

API 契约见 [docs/api-contract.md](docs/api-contract.md)。

## Windows 部署（team_v1.7）

### 单仓库开发

```powershell
cd copilot-serve
.\scripts\bootstrap-windows.ps1
uv run uvicorn main:app --app-dir src --host 127.0.0.1 --port 8765
```

### 仅迁移

```powershell
.\scripts\migrate-windows.ps1
```

### 验收冒烟

服务运行后：

```powershell
.\scripts\smoke-test-windows.ps1
```

### 与 copilot-desktop 集成

生产安装由 **SMC Copilot 安装器** 释放 `runtime\deploy-copilot-serve.ps1`，将本仓库 clone 到 `%LOCALAPPDATA%\Programs\SMC Copilot\runtime\copilot-serve`，并设置用户环境变量 `COPILOT_SERVE_ROOT` / `COPILOT_SERVE_PYTHON`。Desktop Main Process 默认 spawn 本服务（**不**默认启用 Windows Service，避免 8765 端口冲突）。

可选 Windows Service（高级）：

```powershell
uv sync --extra service
uv run ai-copilot-service install
uv run ai-copilot-service start
```

服务名：`HermesLocalService`。勿与 Desktop spawn 同时监听 8765。
