# 房屋租赁系统后端

本目录是纯 FastAPI 后端。应用入口为 `app.main:app`，所有业务接口统一位于 `/api/v1`。

## 本地技术栈

- FastAPI + Uvicorn
- SQLAlchemy 2 + MySQL（PyMySQL 驱动）
- Alembic 数据库迁移
- Redis（房源缓存，可选；不可用时自动回退到进程内 TTL 缓存）
- JWT + Passlib
- LangChain / DeepSeek（对话生成）+ DashScope（RAG 向量嵌入）
- Chroma 向量库（RAG 检索引擎，索引目录 `core/core/chroma_db`）
- 支付宝沙箱支付集成
- Local RAG runbook: [RAG_OPERATIONS.md](RAG_OPERATIONS.md) (sync, rebuild,
  evaluation gate, interrupted-rebuild recovery, local index backup and restore,
  reviewed-feedback export)

## 目录

```text
app/
  api/v1/       FastAPI 路由（10 个子路由，统一挂载在 /api/v1）
  core/         配置、安全、时间与 Redis
  db/           SQLAlchemy 会话与 Base
  models/       SQLAlchemy 模型
  schemas/      通用响应结构（APIResponse / PaginatedData）
  services/     应用服务（AI 代理与工具、查询路由与约束、答案复核、AI 可靠性、
                房源缓存、占用判定、邮件等）
core/           Agent 配置与模型（agent_config、agent_model、agent_utils、prompts）
                以及 RAG 主体（rag/ 索引·检索·评估·反馈导出、data/ 知识语料、
                rag_state/ 索引清单、core/chroma_db 向量库）；由 app/api/v1/chat_ai.py
                与 app/services/react_agent.py 等调用
exts/           支付宝客户端及本地密钥文件
images/         头像与房源图片静态目录（启动时挂载为 /images）
migrations/     Alembic 迁移（versions/ 共 13 个，head = 013_reconciliation_workflow）
tests/          FastAPI 回归测试（14 个文件、172 个测试函数）
alembic.ini           迁移配置（数据库 URL 由 app.core.config 注入）
pytest.ini            测试配置（testpaths=tests，含 integration / unit 标记）
requirements.txt      依赖清单
flaskhousesystem.sql  全量数据库导出（历史库名，不代表仍使用 Flask）
RAG_OPERATIONS.md     RAG 运维手册
start-all.ps1         本地前后端启动脚本
```

## 首次安装

```powershell
cd houseSystemBack-Lu_New_back
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

根据 `.env` 配置 MySQL、JWT（`SECRET_KEY`）、DeepSeek（对话）与 DashScope（向量嵌入）等参数。`app/core/config.py` 为所有字段都提供了默认值，因此开发环境没有 `.env` 也能启动（默认连 `root@localhost:3306/flaskhousesystem`，支付走沙箱 + 本地模拟）；QQ 邮箱、高德地图、OSS 可按需配置。

但 `ENVIRONMENT=production`（或 `prod`）时会强制校验：`SECRET_KEY` 必须改、`DEBUG` 必须关、`PAYMENT_MOCK_ENABLED` 必须关、`CORS_ORIGINS` 必须显式配置，且 **7 个 `ALIPAY_*` 全部必填**、回调与跳转地址必须是 HTTPS、密钥文件必须是合法 PEM。即支付宝在生产环境**不是**「按需配置」。

首次使用空 MySQL 数据库时，必须先导入 `flaskhousesystem.sql`，再执行 Alembic；001 是面向既有旧库的兼容迁移，不是建表迁移。该 SQL 文件名是历史数据库名，不代表应用仍使用 Flask。

## 启动

推荐直接运行：

```powershell
.\start-all.ps1
```

脚本要求：同级目录存在前端工程 `houseSystemFront-Ylfmoonn`、本机可用 `npm`、且已创建 `.venv`，否则直接报错退出。

脚本会先执行 `alembic upgrade head`，然后分别启动：

- 后端：http://127.0.0.1:8000
- 前端：http://localhost:4399（端口由前端工程 `npm run dev` 决定，本脚本只负责启动并提示）
- OpenAPI：http://127.0.0.1:8000/docs

只启动后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

不要再运行根目录 `app.py`；旧入口已经删除。

## 数据库迁移

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q app core exts

# 使用当前 .env 指向的本地 MySQL 执行只读数据集成测试
$env:RUN_MYSQL_INTEGRATION='1'
.\.venv\Scripts\python.exe -m pytest -q tests\test_mysql_integration.py
```

真实 MySQL 集成测试会遍历全部房源分页、价格带、长沙各区县、AI SQL 工具结果和
关键跨表关系；测试本身只读。执行前应先运行 `alembic upgrade head`，当前 head 为
`013_reconciliation_workflow`（共 13 个迁移）。

测试目录共 14 个测试文件、172 个测试函数（多处使用 `@pytest.mark.parametrize`，
实际收集数高于此）。

## 主要接口

- `/api/v1/auth`：注册、登录与邮箱验证码
- `/api/v1/users`：用户资料与管理
- `/api/v1/houses`：房源查询与管理
- `/api/v1/appointments`：创建看房预约
- `/api/v1/houses/{house_id}/comments`、`/api/v1/comments/{comment_id}`：房源留言
- `/api/v1/leases`：创建合同与待签合同（`/leases/pending`）
- `/api/v1/leases/mine`：当前用户的租约记录
- `/api/v1/messages`：站内消息（`/messages`、`/messages/received`）
- `/api/v1/payments`：支付、支付回调与对账
- `/api/v1/chat-ai`：AI 会话（流式入口 `/chat-ai/chat/stream`，含运行状态查询与取消）

同一批路由中还包含：房源核验与房东房源（`/houses/{id}/verification`、
`/houses/landlord/me`）、房源图片上传与统计（`/houses/stats/pie`、`/houses/stats/column`、
`/houses/most-viewed`）、头像与找回密码（`/users/me/avatar`、`/users/password-reset/*`）、
房东升级（`/users/me/landlord`）、AI 反馈闭环（`/chat-ai/runs/{id}/feedback`、
`/chat-ai/failures/{id}/review`）、支付取消/过期/本地模拟确认
（`/payments/{contract_id}/cancel|expire|mock-confirm`）。

`/api/v1` 之外还有非业务端点：`GET /`、存活探针 `GET /healthz`、就绪探针 `GET /readyz`，
以及静态图片目录 `/images`。
