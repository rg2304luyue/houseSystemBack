# 链居 - 房屋租赁系统（后端）

基于 **Flask + SQLAlchemy + MySQL** 的房屋租赁系统后端，提供用户管理、房源管理、合同管理、AI智能选房、即时通讯、支付宝支付等功能。

## 技术栈

| 类别         | 技术                                     |
| ------------ | ---------------------------------------- |
| Web 框架     | Flask                                    |
| ORM          | SQLAlchemy 2.0 + Flask-SQLAlchemy        |
| 数据库       | MySQL 8.0                                |
| 缓存/消息队列 | Redis 6.0+                               |
| 异步任务     | Celery                                   |
| 实时通讯     | Flask-SocketIO                           |
| 认证         | JWT (PyJWT HS256)                        |
| AI/LLM       | 通义千问 DashScope + ReAct Agent         |
| 支付         | 支付宝沙箱 (alipay-sdk-python)            |
| 邮件         | QQ邮箱 SMTP                              |
| 对象存储     | 阿里云 OSS                               |
| OAuth        | GitHub OAuth                             |
| 容器化       | Docker + Docker Compose                  |

## 项目结构

```
houseSystemBack-Lu_New_back/
├── app.py                       # Flask 应用入口，蓝图注册，SocketIO / Celery 初始化
├── config.py                    # 集中配置（DB / Redis / Celery / OAuth / OSS / AI）
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
├── Dockerfile                   # Docker 镜像构建
├── docker-compose.yml           # 一键编排（backend + frontend + MySQL + Redis）
│
├── blueprints/                  # 路由蓝图（Controller 层，16 个模块）
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
│   └── celery_bp.py             # Celery 异步任务
│
├── services/                    # 业务逻辑层（12 个服务）
│   ├── user_service.py
│   ├── house_info_service.py
│   ├── housedetil_service.py
│   ├── comment_service.py
│   ├── contract_service.py
│   ├── appointment_service.py
│   ├── repair_service.py
│   ├── message_service.py
│   ├── channel_service.py
│   ├── news_service.py
│   └── rental_service.py
│
├── models/                      # 数据模型层（全部使用 db.Model + Mapped 语法）
│   ├── user_model.py            # UserModel
│   ├── house_model.py           # HouseInfo
│   ├── house_detail_model.py    # HouseDetail
│   ├── appointment_model.py     # AppointmentModel
│   ├── comment_model.py         # Comment
│   ├── contract_model.py        # Contract
│   ├── repair_complaint_model.py # Repair_Complaint
│   ├── message_model.py         # Message
│   ├── channel_model.py         # Channel
│   ├── news_model.py            # News
│   ├── rental_model.py          # Rental
│   ├── chat_model.py            # ChatSession + ChatMessage
│   └── log_model.py             # LogEntry
│
├── core/                        # AI 核心模块
│   ├── agent/                   # ReAct Agent + 工具集
│   ├── agent_config/            # Agent 配置
│   ├── agent_model/             # Agent 数据模型
│   ├── agent_utils/             # Agent 工具函数
│   ├── core/                    # 核心编排
│   ├── prompts/                 # Prompt 模板
│   ├── rag/                     # RAG 检索增强
│   └── data/                    # 静态数据
│
├── exts/                        # 扩展初始化
│   ├── db.py                    # SQLAlchemy 实例
│   ├── cors.py                  # CORS 配置
│   ├── redis.py                 # Redis 连接 + 缓存工具
│   ├── celery.py                # Celery 实例 + 工厂方法
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
- Redis 6.0+

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入实际值
# 必填: MYSQL_PASSWORD, SECRET_KEY
# 按需: DASHSCOPE_API_KEY, GITHUB_CLIENT_ID 等
```

### 2. 安装依赖

```bash
python -m venv flask_env
# Windows
flask_env\Scripts\activate
# Linux/Mac
source flask_env/bin/activate

pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS flaskhousesystem DEFAULT CHARSET utf8mb4;"

# 导入初始数据（如有 SQL 文件）
mysql -u root -p flaskhousesystem < flaskhousesystem.sql
```

### 4. 启动 Redis

```bash
# Docker 方式
docker run -d -p 6379:6379 redis:6.2-alpine

# 或本地
redis-server
```

### 5. 启动 Celery（可选，异步邮件）

```bash
celery -A app.celery worker --loglevel=info -P threads
```

### 6. 启动服务

```bash
python app.py
# 服务启动在 http://localhost:5000
```

## Docker 一键部署

```bash
# 在 houseSystemBack-Lu_New_back 目录下
docker-compose up -d --build

# 同时启动：MySQL + Redis + 后端(5000) + 前端(80)

# 查看日志
docker-compose logs -f backend

# 停止
docker-compose down
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
                           │ /api/* /user/* ...
                    ┌──────▼──────┐
                    │   Flask     │  ← 后端容器 :5000
                    │  (Python)   │
                    └──┬────┬──┬──┘
                       │    │  │
              ┌────────▼┐ ┌─▼──▼─┐
              │  MySQL  │ │ Redis│
              └─────────┘ └──────┘
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

### AI 流式对话示例

```bash
curl -X POST http://localhost:5000/chat-ai/chat/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我推荐岳麓区2000元以内的两室一厅", "session_id": null}'
```

响应为 SSE 流：`data: {"type": "chunk", "content": "..."}` → `data: {"type": "done", "session_id": 42}`

### 支付流程

```
前端 → POST /api/alipay/pay → 获取 pay_url → 跳转支付宝收银台
                                         → 支付完成 → 同步回跳 /api/alipay/return
                                         → 异步通知 /api/alipay/notify → 更新订单状态
```

## 环境变量

| 变量名                      | 说明                      | 必填 |
| --------------------------- | ------------------------- | ---- |
| `MYSQL_USER`                | 数据库用户名               | 否   |
| `MYSQL_PASSWORD`            | 数据库密码                 | 是   |
| `MYSQL_HOST`                | 数据库主机                 | 否   |
| `MYSQL_PORT`                | 数据库端口                 | 否   |
| `MYSQL_DB`                  | 数据库名称                 | 否   |
| `SECRET_KEY`                | Flask/JWT 密钥            | 是   |
| `REDIS_URL`                 | Redis 连接地址             | 否   |
| `DASHSCOPE_API_KEY`         | 通义千问 API Key           | 按需 |
| `GITHUB_CLIENT_ID`          | GitHub OAuth Client ID    | 按需 |
| `GITHUB_CLIENT_SECRET`      | GitHub OAuth Secret       | 按需 |
| `GITHUB_CALLBACK_URL`       | GitHub OAuth 回调地址      | 按需 |
| `OSS_ACCESS_KEY_ID`         | 阿里云 OSS AccessKey      | 按需 |
| `OSS_ACCESS_KEY_SECRET`     | 阿里云 OSS Secret         | 按需 |
| `GAODE_WEATHER_KEY`         | 高德地图 API Key           | 按需 |
| `GAODE_MAP_KEY`             | 高德地图 Key               | 按需 |
| `GAODE_MAP_SAFE_KEY`        | 高德地图安全 Key           | 按需 |
| `SMTP_SENDER_EMAIL`         | QQ邮箱发件人地址           | 按需 |
| `SMTP_AUTH_CODE`            | QQ邮箱 SMTP 授权码         | 按需 |

> 支付宝密钥通过 `exts/` 目录下的 `app_private_key.txt` 和 `alipay_public_key.txt` 文件管理（已在 .gitignore 中排除）。
> 沙箱环境需在支付宝开放平台启用"公钥模式"并上传公钥。
