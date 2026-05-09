# 链居 - 房屋租赁系统（后端）

基于 **Flask + SQLAlchemy + MySQL** 的房屋租赁系统后端，提供用户管理、房源管理、合同管理、AI智能选房、即时通讯、支付宝支付等功能。

## 技术栈

| 类别         | 技术                                     |
| ------------ | ---------------------------------------- |
| Web 框架     | Flask                                    |
| ORM          | SQLAlchemy 2.0 + Flask-SQLAlchemy        |
| 数据库       | MySQL 8.0                                |
| 缓存 / 消息队列 | Redis 7                                |
| 异步任务     | Celery                                   |
| 实时通讯     | Flask-SocketIO                           |
| 认证         | JWT (PyJWT HS256)                        |
| AI/LLM       | 通义千问 DashScope + ReAct Agent + RAG   |
| 支付         | 支付宝沙箱 (alipay-sdk-python)            |
| 邮件         | QQ邮箱 SMTP                              |
| 对象存储     | 阿里云 OSS                               |
| OAuth        | GitHub OAuth                             |
| 容器化       | Docker + Docker Compose                  |

## 项目结构

```
houseSystemBack-Lu_New_back/
├── app.py                       # Flask 应用入口，蓝图注册，SocketIO / Celery 初始化
├── config.py                    # 配置类（从环境变量读取，无硬编码密钥，git 可追踪）
├── requirements.txt             # Python 依赖（249 个，已清理无用包）
├── .env.example                 # 环境变量模板（部署时复制为 .env 填入真实值）
├── .env                         # 本地密钥（已在 .gitignore 中排除）
├── Dockerfile                   # Docker 镜像构建
├── docker-compose.yml           # 一键编排（backend + celery + frontend + MySQL + Redis）
│
├── blueprints/                  # 路由蓝图（16 个模块）
│   ├── user.py                  # /user        — 注册/登录/资料/头像/密码重置
│   ├── houseinfo.py             # /houseinfo   — 房源 CRUD + 搜索筛选 + 统计图表
│   ├── housedetail.py           # /housedetail — 房源详情（图片/设施/地图坐标）
│   ├── comment.py               # /comments    — 房源评论
│   ├── contract.py              # /contracts   — 租房合同
│   ├── appointment.py           # /appointments— 看房预约
│   ├── repair_complaint.py      # /repaires    — 维修申报/投诉
│   ├── message.py               # /messages    — REST + Socket.IO 即时通讯
│   ├── news.py                  # /news        — 新闻资讯 CRUD
│   ├── rental.py                # /rental      — 租房记录
│   ├── log_management.py        # /admin/logs  — 系统日志管理
│   ├── chat_ai.py               # /chat-ai     — AI 智能选房 + SSE 流式对话
│   ├── alipay.py                # /api/alipay  — 支付宝支付
│   ├── github.py                # /github      — GitHub OAuth 登录
│   ├── email_auth.py            # /email-auth  — 邮箱验证码登录
│   └── celery_bp.py             # Celery 异步任务（邮件发送、GitHub 数据获取）
│
├── services/                    # 业务逻辑层（12 个服务）
├── models/                      # 数据模型层（13 个模型，db.Model + Mapped 语法）
│
├── core/                        # AI 核心模块
│   ├── agent/                   # ReAct Agent + 工具集（搜索/天气/通勤/市场）
│   ├── rag/                     # RAG 检索增强（ChromaDB 向量存储）
│   ├── prompts/                 # Prompt 模板
│   └── agent_config/            # Agent / RAG / ChromaDB 配置
│
├── exts/                        # 扩展初始化
│   ├── db.py                    # SQLAlchemy 实例
│   ├── cors.py                  # CORS 配置
│   ├── redis.py                 # Redis 连接 + 缓存工具
│   ├── celery.py                # Celery 实例 + 平台自适应（Windows solo / Linux prefork）
│   ├── alipay.py                # 支付宝常量 + 密钥加载
│   ├── alipay_client.py         # 支付宝 SDK 封装
│   └── log_handlers.py          # 数据库日志处理器
│
├── decorators/
│   └── decorators.py            # @token_required JWT 认证装饰器
│
├── utils/
│   └── response_utils.py        # 统一响应格式 {code, data, message, success}
│
└── images/                      # 用户头像上传目录
```

## 快速开始

### 前置要求

- Python 3.10+
- MySQL 8.0+
- Redis 7.0+

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入实际值
# 必填: MYSQL_PASSWORD, SECRET_KEY, QQ_SMTP_EMAIL, QQ_SMTP_AUTH_CODE
# 按需: DASHSCOPE_API_KEY, GITHUB_CLIENT_ID 等
```

> `python-dotenv` 会自动加载 `.env` 文件。Docker 部署时 docker-compose 读取 `.env` 注入环境变量。

### 2. 安装依赖

```bash
python -m venv flask_env
# Windows: flask_env\Scripts\activate
# Linux/Mac: source flask_env/bin/activate

pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS flaskhousesystem DEFAULT CHARSET utf8mb4;"
mysql -u root -p flaskhousesystem < flaskhousesystem.sql
```

### 4. 启动服务

```bash
# 终端1: Redis
redis-server

# 终端2: Celery Worker（邮件异步发送）
# Windows:
celery -A app:celery worker --loglevel=info --pool=solo
# Linux/Docker:
celery -A app:celery worker --loglevel=info --concurrency=4

# 终端3: Flask
python app.py
# 服务启动在 http://localhost:5000
```

## Docker 一键部署

```bash
docker compose up -d --build

# 同时启动：MySQL + Redis + Flask(5000) + Celery Worker + 前端 Nginx(80)

# 查看日志
docker compose logs -f backend

# 停止
docker compose down
```

### 服务架构

```
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │ :80
                    ┌──────▼──────┐
                    │   Nginx     │  ← 前端容器
                    │  (Vue SPA)  │
                    └──────┬──────┘
                           │ API 代理
                    ┌──────▼──────┐
                    │   Flask     │  ← 后端容器 :5000
                    │  (Gunicorn) │
                    └──┬──┬──┬──┬─┘
                       │  │  │  │
              ┌────────▼┐ │  │  ┌──────────────┐
              │  MySQL  │ │  │  │ Celery Worker│ ← 异步邮件
              └─────────┘ │  │  └──────┬───────┘
                          │  │         │
              ┌───────────▼──▼──▼─────▼┐
              │        Redis           │ ← 缓存 + 消息队列
              └────────────────────────┘
```

## API 概览

所有接口统一返回格式：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

### 模块总览

| 前缀           | 模块         | 关键端点                              |
| -------------- | ------------ | ------------------------------------- |
| `/user`        | 用户         | register, login, email-login, userinfo |
| `/houseinfo`   | 房源         | CRUD, 筛选/分页, 统计图表              |
| `/housedetail` | 房源详情     | 图片/设施/地图坐标                      |
| `/comments`    | 评论         | 获取房源评论, 添加评论                  |
| `/contracts`   | 合同         | 创建/查询合同                          |
| `/appointments`| 看房预约     | 创建预约                              |
| `/repaires`    | 维修投诉     | 提交维修/投诉                          |
| `/messages`    | 即时通讯     | REST 消息 + Socket.IO 事件             |
| `/news`        | 新闻         | CRUD, 分页                            |
| `/rental`      | 租房记录     | 按租客/房东查询                        |
| `/chat-ai`     | AI 选房      | 流式对话 (SSE), 会话管理               |
| `/api/alipay`  | 支付         | 生成支付链接, 异步回调                  |
| `/github`      | GitHub OAuth | 第三方登录                            |
| `/email-auth`  | 邮箱验证     | 发送验证码, 验证登录                    |
| `/admin/logs`  | 系统日志     | 日志查看/删除                          |

### 认证

- JWT Token 有效期 24 小时
- 需认证的接口携带请求头: `Authorization: Bearer <token>`
- Socket.IO 连接需先发送 `authenticate` 事件

### 支付流程

```
前端 → POST /api/alipay/pay → 获取 pay_url → 跳转支付宝收银台
                                         → 支付完成 → 同步回跳 /api/alipay/return
                                         → 异步通知 /api/alipay/notify → 更新订单状态
```

## 环境变量

| 变量名               | 说明                      | 必填 |
| -------------------- | ------------------------- | ---- |
| `MYSQL_USER`         | 数据库用户名               | 否   |
| `MYSQL_PASSWORD`     | 数据库密码                 | 是   |
| `MYSQL_HOST`         | 数据库主机                 | 否   |
| `MYSQL_PORT`         | 数据库端口                 | 否   |
| `MYSQL_DB`           | 数据库名称                 | 否   |
| `SECRET_KEY`         | Flask/JWT 密钥            | 是   |
| `REDIS_URL`          | Redis 连接地址             | 否   |
| `QQ_SMTP_EMAIL`      | QQ邮箱发件人地址           | 是   |
| `QQ_SMTP_AUTH_CODE`  | QQ邮箱 SMTP 授权码         | 是   |
| `DASHSCOPE_API_KEY`  | 通义千问 API Key           | 按需 |
| `GAODE_WEATHER_KEY`  | 高德天气 API Key           | 按需 |
| `GAODE_MAP_KEY`      | 高德地图 Key               | 按需 |
| `GAODE_MAP_SAFE_KEY` | 高德地图安全 Key           | 按需 |
| `GITHUB_CLIENT_ID`   | GitHub OAuth Client ID     | 按需 |
| `GITHUB_CLIENT_SECRET`| GitHub OAuth Secret       | 按需 |
| `GITHUB_CALLBACK_URL` | GitHub OAuth 回调地址     | 按需 |
| `OSS_ACCESS_KEY_ID`  | 阿里云 OSS AccessKey       | 按需 |
| `OSS_ACCESS_KEY_SECRET`| 阿里云 OSS Secret        | 按需 |

> 支付宝密钥通过 `exts/` 目录下的 `app_private_key.txt` 和 `alipay_public_key.txt` 文件管理（已在 .gitignore 中排除）。

## 配置管理

- **`config.py`** — 定义 `Config` 类，所有值从环境变量读取，默认值为空字符串或安全占位符。**可在 git 中追踪。**
- **`.env`** — 本地密钥文件，被 `.gitignore` 排除，部署时手动创建。
- **`.env.example`** — 模板文件，包含所有需要的变量名。
- **Docker** — docker-compose 自动读取 `.env` 注入容器环境变量。
