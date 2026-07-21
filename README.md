# 房屋租赁系统后端

本目录是纯 FastAPI 后端。应用入口为 `app.main:app`，所有业务接口统一位于 `/api/v1`。

## 本地技术栈

- FastAPI + Uvicorn
- SQLAlchemy 2 + MySQL
- Alembic 数据库迁移
- Redis（房源缓存，可选；不可用时自动回退）
- JWT + Passlib
- LangChain / DashScope AI 助手
- 支付宝沙箱支付集成

## 目录

```text
app/
  api/v1/       FastAPI 路由
  core/         配置、安全和 Redis
  db/           SQLAlchemy 会话与 Base
  models/       SQLAlchemy 模型
  schemas/      通用响应结构
  services/     邮件等应用服务
core/           AI 模型与提示词（由 FastAPI AI 路由使用）
exts/           支付宝客户端及本地密钥文件
migrations/     Alembic 迁移
tests/          FastAPI 回归测试
start-all.ps1   本地前后端启动脚本
```

## 首次安装

```powershell
cd houseSystemBack-Lu_New_back
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

根据 `.env` 配置 MySQL、JWT、DashScope 等参数。首次使用空 MySQL 数据库时，必须先导入 `flaskhousesystem.sql`，再执行 Alembic；001 是面向既有旧库的兼容迁移，不是建表迁移。该 SQL 文件名是历史数据库名，不代表应用仍使用 Flask。

## 启动

推荐直接运行：

```powershell
.\start-all.ps1
```

脚本会先执行 `alembic upgrade head`，然后分别启动：

- 后端：http://127.0.0.1:8000
- 前端：http://localhost:4399
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

## Docker deployment

```powershell
docker compose up -d --build
docker compose ps
docker compose logs migrate
```

The MySQL image imports `flaskhousesystem.sql` only when `mysql_data` is
empty. That dump already contains the FastAPI schema and is stamped at the
current Alembic head. Existing MySQL volumes are not re-imported; the one-shot
`migrate` service upgrades them before the API starts. Do not run
`docker compose down -v` against an environment whose database must be kept.

After deployment, verify both migration state and readiness:

```powershell
docker compose exec backend python -m alembic current
curl.exe -f http://localhost:8000/readyz
curl.exe -f http://localhost/
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q app core exts
```

## 主要接口

- `/api/v1/auth`：注册和登录
- `/api/v1/users`：用户资料与管理
- `/api/v1/houses`：房源查询与管理
- `/api/v1/appointments`：预约看房
- `/api/v1/comments`：房源留言
- `/api/v1/leases`：合同
- `/api/v1/rentals`：租约
- `/api/v1/payments`：支付状态与回调
- `/api/v1/chat-ai`：AI 会话
