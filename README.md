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
