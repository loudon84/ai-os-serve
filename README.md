# ai-copilot-serve

ai-os-desktop 本地控制面：Hermes Profile、Gateway 启停、models/runs 代理。

## 开发

```bash
cd ai-copilot-serve
cp .env.example .env
pip install -e ".[dev]"
alembic upgrade head
uvicorn ai_copilot_serve.main:app --reload --host 127.0.0.1 --port 8765
```

## 迁移

```bash
alembic upgrade head
```

## 测试

```bash
pytest
```

API 契约见 [docs/api-contract.md](docs/api-contract.md)。
