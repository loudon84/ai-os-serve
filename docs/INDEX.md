# ai-copilot-serve — 文档索引

> 本地控制面服务：Hermes Gateway 管理、任务调度、审批门控、工作空间安全策略。
> 本索引面向 Agent 与开发者，用于按需加载项目文档。

---

## 一、项目定位

`ai-copilot-serve` 是面向 **ai-os-desktop** 的本地控制面服务，职责：

- Hermes Gateway Profile 管理（CRUD / 启停 / 健康检查）
- Hermes Run 代理（模型列表 / 运行 / 事件流）
- 本地任务运行时（创建 / 执行 / 取消 / 状态机）
- 团队任务同步（Team Hub 拉取 / 认领 / Outbox 回写）
- 审批门控（申请 / 批准 / 拒绝）
- 工作空间安全策略（路径校验 / 命令分类 / Workspace Guard）
- 任务路由规则（profile_type / require_approval）
- 桌面工作台摘要

**不负责**：Agent 推理引擎实现、Hermes Gateway 进程内部逻辑、Electron UI 渲染。

---

## 二、技术栈

| 层 | 选型 |
|---|---|
| 语言 | Python 3.12 |
| API 框架 | FastAPI |
| ASGI 服务器 | Uvicorn |
| DTO / 契约 | Pydantic v2 |
| 配置 | pydantic-settings |
| ORM | SQLAlchemy 2.x async |
| 数据库 | SQLite (aiosqlite，local-first desktop state) |
| 迁移 | Alembic |
| 出站 HTTP | httpx |
| 进程管理 | asyncio subprocess + psutil |
| 测试 | pytest / pytest-asyncio |
| 包管理 | uv |

---

## 三、工程目录结构

```text
ai-os-api/
├── src/                                    # 扁平源码根 (pythonpath / --app-dir src)
│   ├── __init__.py                         #   包声明
│   ├── main.py                             #   入口: main:app
│   ├── app.py                              #   FastAPI 应用工厂 create_app()
│   ├── api/
│   │   ├── deps.py                         #     依赖注入
│   │   ├── router.py                       #     API 路由聚合 (prefix=/api/v1)
│   │   └── v1/                             #     V1 路由端点
│   │       ├── health.py                   #       健康检查
│   │       ├── system.py                   #       系统信息
│   │       ├── profiles.py                 #       Profile CRUD + 启停
│   │       ├── gateways.py                 #       Gateway 健康/日志
│   │       ├── hermes_runs.py              #       Hermes Run 代理
│   │       ├── tasks.py                    #       本地任务
│   │       ├── team_tasks.py               #       团队任务绑定
│   │       ├── task_routing.py             #       任务路由规则
│   │       ├── approvals.py                #       审批
│   │       ├── workspaces.py               #       工作空间
│   │       └── desktop_workbench.py        #       桌面工作台摘要
│   ├── core/
│   │   ├── config.py                       #   全局配置 (pydantic-settings)
│   │   ├── constants.py                    #   常量定义
│   │   ├── enums.py                        #   枚举类型
│   │   ├── errors.py                       #   CopilotError 异常类
│   │   ├── lifecycle.py                    #   FastAPI lifespan 管理
│   │   ├── logging.py                      #   日志配置
│   │   └── task_routing.py                 #   任务路由逻辑
│   ├── db/
│   │   ├── base.py                         #   SQLAlchemy DeclarativeBase
│   │   ├── session.py                      #   async engine & session factory
│   │   ├── models/
│   │   │   ├── __init__.py                 #     模型导出
│   │   │   ├── profile.py                  #     Profile 模型
│   │   │   ├── local_task.py               #     LocalTask 模型
│   │   │   ├── task_related.py             #     SyncOutbox / TaskEvent / TeamTaskBinding / AuditLog
│   │   │   └── workspace_db.py             #     Workspace 模型
│   │   └── repositories/
│   │       ├── profile_repo.py             #     Profile 仓库
│   │       └── v12_repos.py                #     V1.2 仓库 (task/approval/workspace)
│   ├── schemas/
│   │   ├── common.py                       #   ErrorResponse 等通用 schema
│   │   ├── profile.py                      #   Profile DTO
│   │   ├── gateway.py                      #   Gateway DTO
│   │   ├── hermes.py                       #   Hermes DTO
│   │   ├── system.py                       #   System DTO
│   │   └── v12_tasks.py                    #   V1.2 任务/审批/工作空间 DTO
│   ├── services/
│   │   ├── profile_service.py              #   Profile 业务逻辑
│   │   ├── gateway_supervisor.py           #   Gateway 进程监督
│   │   ├── hermes_gateway_client.py        #   Hermes Gateway HTTP 客户端
│   │   ├── task_runtime.py                 #   任务运行时
│   │   ├── task_state_machine.py           #   任务状态机
│   │   ├── task_sync_service.py            #   任务同步服务
│   │   ├── task_routing_registry.py        #   任务路由注册
│   │   ├── approval_service.py             #   审批服务
│   │   ├── workspace_guard.py              #   工作空间安全守卫
│   │   └── workbench_summary.py            #   工作台摘要服务
│   ├── integrations/
│   │   ├── hermes/
│   │   │   ├── client.py                   #     Hermes Gateway HTTP 客户端
│   │   │   ├── config_writer.py            #     Hermes 配置文件写入
│   │   │   └── profile_loader.py           #     Hermes 配置文件加载
│   │   └── team_hub/
│   │       ├── client.py                   #     Team Hub 远程客户端 (Stub / HTTP)
│   │       ├── dto.py                      #     Team Hub DTO
│   │       └── errors.py                   #     Team Hub 错误定义
│   ├── runtime/
│   │   ├── gateway_process.py              #   网关进程管理
│   │   └── port_allocator.py              #   端口分配器
│   ├── workers/
│   │   └── v12_workers.py                  #   V1.2 后台工作线程 (轮询/同步/健康检查)
│   └── utils/
│       └── paths.py                        #   路径工具函数
├── migrations/                              # Alembic 迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_create_profiles.py
│       └── 0002_v12_tables.py
├── tests/
│   ├── conftest.py                          # pytest 配置和 fixtures
│   ├── test_v1_acceptance.py               # V1 API 验收测试
│   ├── test_v12_integration.py             # V1.2 集成测试
│   ├── test_checksum.py                    # 校验和测试
│   ├── test_version_conflict.py            # 版本冲突测试
│   ├── test_permission_service.py          # 权限服务测试
│   └── test_snapshot_save_schema.py        # 快照保存 schema 测试
├── scripts/
│   ├── mock_hermes_gateway.py              # 模拟 Hermes 网关 (开发/测试用)
│   └── smoke-test.ps1                      # PowerShell 冒烟测试脚本
├── docs/
│   ├── INDEX.md                            # 本文件
│   └── api-contract.md                     # API 契约文档
├── prd/
│   ├── ver1.0.md                           # V1.0 需求
│   ├── ver1.2.md                           # V1.2 需求
│   └── ver1.3.md                           # V1.3 需求
├── app/                                    # [旧版] 前端数据层代码 (documents 模块, 端口 8000)
├── pyproject.toml
├── alembic.ini
├── .env.example
├── AGENT.md
└── README.md
```

---

## 四、已实现模块

### 4.1 System / Health

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/health`, `/api/v1/system` |
| 端点 | 健康检查、系统版本/路径信息 |

### 4.2 Profiles 模块

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/profiles` |
| 数据表 | `profiles` |
| 功能 | Profile CRUD、Gateway 启停、状态查询 |

### 4.3 Gateways 模块

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/gateways` |
| 功能 | Gateway 健康检查、日志尾部读取 |

### 4.4 Hermes Proxy 模块

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/profiles/{profile_id}/models`, `/api/v1/profiles/{profile_id}/runs` |
| 功能 | 代理 Hermes Gateway 的模型列表、Run 创建/查询/事件流 |

### 4.5 Tasks 模块 (V1.2)

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/tasks` |
| 数据表 | `local_tasks`, `task_events` |
| 功能 | 本地任务 CRUD、执行/取消、绑定 Profile、事件日志、SSE 流、审批申请 |

### 4.6 Team Tasks 模块 (V1.2)

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/team-tasks` |
| 数据表 | `team_task_bindings`, `sync_outbox` |
| 功能 | Hub 拉取/认领、绑定列表、Outbox 同步 |

### 4.7 Task Routing 模块 (V1.2)

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/task-routing` |
| 功能 | 路由规则查询/更新 (profile_type / require_approval) |

### 4.8 Approvals 模块 (V1.2)

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/approvals` |
| 数据表 | `approvals` |
| 功能 | 审批列表/待审、批准/拒绝 |

### 4.9 Workspaces 模块 (V1.2)

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/workspaces` |
| 数据表 | `workspaces` |
| 功能 | 工作空间 CRUD、路径校验、命令分类 |

### 4.10 Desktop Workbench 模块 (V1.2)

| 分类 | 说明 |
|---|---|
| API 前缀 | `/api/v1/desktop/task-workbench` |
| 功能 | 工作台摘要 (profiles/tasks/approvals 按状态计数) |

---

## 五、规划模块

### 5.1 Local Shell 集成（规划中）

- 命令执行器与命令策略
- Shell 执行须经 Workspace Guard 和 Approval Runtime 仲裁

### 5.2 Audit 日志模块（规划中）

- 操作审计日志查询 API (`/api/v1/audit`)

---

## 六、索引维护规则

新增模块或文档时**必须**同步更新本文件：

1. 在「已实现模块」或「规划模块」中增加对应条目。
2. 更新目录结构树。
3. 同步更新 `docs/api-contract.md` 和 `AGENT.md` 中相关描述。
