# 房屋租赁系统 - 后端

基于 **Flask** 的房屋租赁系统后端，提供用户管理、房源管理、合同管理、AI智能选房、即时通讯、支付宝支付等功能。

## 技术栈

| 类别         | 技术                                     |
| ------------ | ---------------------------------------- |
| Web 框架     | Flask                                    |
| ORM          | SQLAlchemy + Flask-SQLAlchemy            |
| 数据库       | MySQL                                    |
| 缓存/消息队列 | Redis                                    |
| 异步任务     | Celery                                   |
| 实时通讯     | Flask-SocketIO                           |
| 认证         | JWT (PyJWT)                              |
| AI/LLM       | 通义千问 DashScope + ReAct Agent         |
| AI Tools     | MCP (Model Context Protocol)             |
| RAG          | 自建向量检索 + 嵌入服务                   |
| 支付         | 支付宝沙箱 (alipay-sdk-python)            |
| 邮件         | QQ邮箱 SMTP                              |
| 对象存储     | 阿里云 OSS                               |
| OAuth        | GitHub OAuth                             |
| 容器化       | Docker + Docker Compose                  |

## 项目结构

```
houseSystemBack-Lu_New_back/
├── app.py                       # Flask 应用入口，蓝图注册，启动配置
├── config.py                    # 配置文件（需自行创建，见下方说明）
├── socketio_init.py             # Socket.IO 实例初始化
├── requirements.txt             # Python 依赖列表
├── Dockerfile                   # Docker 镜像构建文件
├── docker-compose.yml           # Docker Compose 编排（MySQL + Redis + App）
├── flaskhousesystem.sql         # 数据库初始化 SQL 文件
│
├── blueprints/                  # 路由蓝图（Controller 层）
│   ├── user.py                  # 用户相关接口（注册/登录/资料/头像）
│   ├── houseinfo.py             # 房源信息接口（CRUD + 搜索 + 统计）
│   ├── housedetail.py           # 房源详情接口（图片/设施/地图）
│   ├── comment.py               # 评论接口
│   ├── contract.py              # 合同接口
│   ├── appointment.py           # 看房预约接口
│   ├── repair_complaint.py      # 维修申报/投诉接口
│   ├── message.py               # 即时通讯接口（REST + Socket.IO）
│   ├── news.py                  # 新闻资讯接口
│   ├── rental.py                # 租房记录接口
│   ├── log_management.py        # 系统日志管理接口
│   ├── chat_ai.py               # AI 智能选房 + 流式对话接口
│   ├── alipay.py                # 支付宝支付接口
│   ├── github.py                # GitHub OAuth 登录接口
│   ├── email_auth.py            # 邮箱验证码登录接口
│   └── celery_bp.py             # Celery 异步任务定义
│
├── services/                    # 业务逻辑层
│   ├── user_service.py          # 用户业务逻辑
│   ├── house_info_service.py    # 房源业务逻辑
│   ├── housedetil_service.py    # 房源详情业务逻辑
│   ├── comment_service.py       # 评论业务逻辑
│   ├── contract_service.py      # 合同业务逻辑
│   ├── appointment_service.py   # 预约业务逻辑
│   ├── repair_service.py        # 维修投诉业务逻辑
│   ├── message_service.py       # 消息业务逻辑
│   ├── channel_service.py       # 聊天频道业务逻辑
│   ├── news_service.py          # 新闻业务逻辑
│   └── rental_service.py        # 租房记录业务逻辑
│
├── models/                      # 数据模型层
│   ├── models.py                # 所有 ORM 模型定义（User/Contract/Message/ChatSession 等）
│   ├── house_model.py           # 房源模型（HouseInfo）
│   ├── house_detail_model.py    # 房源详情模型（HouseDetail）
│   ├── user_model.py            # 用户模型（UserModel）
│   ├── appointment_model.py     # 预约模型
│   └── log_model.py             # 日志模型
│
├── core/                        # AI 核心模块
│   ├── agent/
│   │   ├── react_agent.py       # ReAct 模式的 AI Agent
│   │   └── tools/
│   │       ├── agent_tools.py   # Agent 工具集（搜索房源等）
│   │       ├── mcp_tools.py     # MCP 协议工具
│   │       └── middleware.py    # 中间件
│   ├── agent_model/
│   │   └── factor.py            # Agent 模型因子
│   ├── agent_utils/
│   │   ├── config_handler.py    # 配置处理器
│   │   ├── file_handler.py      # 文件处理器
│   │   ├── path_tool.py         # 路径工具
│   │   └── prompt_loader.py     # Prompt 加载器
│   └── rag/
│       ├── rag_service.py       # RAG 检索增强服务
│       └── vector_store.py      # 向量存储
│
├── exts/                        # 扩展初始化
│   ├── db.py                    # SQLAlchemy 实例
│   ├── cors.py                  # CORS 跨域配置
│   ├── redis.py                 # Redis 连接 + 缓存工具类
│   ├── celery.py                # Celery 实例 + 工厂方法
│   ├── alipay.py                # 支付宝常量配置
│   ├── alipay_client.py         # 支付宝 SDK 客户端封装
│   └── log_handlers.py          # 数据库日志处理器
│
├── decorators/
│   └── decorators.py            # 装饰器（@token_required JWT认证）
│
├── utils/
│   └── response_utils.py        # 统一响应格式 + 状态码
│
└── images/                      # 用户头像上传目录
```

## 快速开始

### 前置要求

- Python 3.10+
- MySQL 5.7+（或 8.0+）
- Redis 6.0+
- Docker & Docker Compose（可选，用于容器化部署）

### 1. 克隆项目

```bash
git clone <repo-url>
cd houseSystemBack-Lu_New_back
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv flask_env
# Windows
flask_env\Scripts\activate
# Linux/Mac
source flask_env/bin/activate

pip install -r requirements.txt
```

### 3. 创建配置文件 `config.py`

> **重要**: 项目根目录下的 `config.py` 包含所有敏感密钥，**不会**提交到 Git。你需要自行创建。

在项目根目录创建 `config.py`，参考以下模板：

```python
# config.py
import os
import secrets

def _env(key, default=None):
    return os.environ.get(key, default)

class Config:
    # ─── 数据库 ───
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_env('MYSQL_USER', '你的数据库用户名')}"
        f":{_env('MYSQL_PASSWORD', '你的数据库密码')}"
        f"@{_env('MYSQL_HOST', 'localhost')}"
        f":{_env('MYSQL_PORT', '3306')}"
        f"/{_env('MYSQL_DB', 'flaskhousesystem')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = _env('SECRET_KEY') or secrets.token_hex(32)
    JSON_AS_ASCII = False
    STRICT_SLASH = False

    # ─── Redis ───
    REDIS_URL = _env('REDIS_URL', 'redis://@localhost:6379/0')

    # ─── Celery ───
    CELERY_BROKER_URL = _env('CELERY_BROKER_URL', 'redis://@localhost:6379/1')
    CELERY_RESULT_BACKEND = _env('CELERY_RESULT_BACKEND', 'redis://@localhost:6379/1')
    CELERY_ACCEPT_CONTENT = ['application/json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'Asia/Shanghai'

    # ─── GitHub OAuth ───
    GITHUB_CLIENT_ID = _env('GITHUB_CLIENT_ID', '你的GitHub Client ID')
    GITHUB_CLIENT_SECRET = _env('GITHUB_CLIENT_SECRET', '你的GitHub Client Secret')
    GITHUB_CALLBACK_URL = _env('GITHUB_CALLBACK_URL', 'http://127.0.0.1:5000/github/callback')

    # ─── 阿里云 OSS ───
    OSS_ACCESS_KEY_ID = _env('OSS_ACCESS_KEY_ID', '你的OSS AccessKey')
    OSS_ACCESS_KEY_SECRET = _env('OSS_ACCESS_KEY_SECRET', '你的OSS Secret')
    OSS_BUCKET_NAME = _env('OSS_BUCKET_NAME', '你的Bucket名称')
    OSS_ENDPOINT = _env('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')

    # ─── 通义千问 AI ───
    DASHSCOPE_API_KEY = _env('DASHSCOPE_API_KEY', '你的DashScope API Key')

    # ─── 高德地图 ───
    GaoDeWeatherKey = _env('GAODE_WEATHER_KEY', '你的高德API Key')

    # ─── 邮件 (QQ邮箱SMTP授权码，通过环境变量配置) ───
    # 详见下方"密钥配置清单" -> SMTP 邮件

    # ─── 支付宝 (通过环境变量配置) ───
    # 详见下方"密钥配置清单" -> 支付宝
```

### 密钥配置清单

> 以下所有密钥均通过**环境变量**配置，不硬编码在代码中。可创建 `.env` 文件（已加入 `.gitignore`）统一管理。

| 服务           | 环境变量                     | 说明                          | 获取地址                                                   |
| -------------- | ---------------------------- | ----------------------------- | ---------------------------------------------------------- |
| 数据库         | `MYSQL_USER`                 | MySQL 用户名                   | -                                                          |
| 数据库         | `MYSQL_PASSWORD`             | MySQL 密码                     | -                                                          |
| 数据库         | `MYSQL_HOST`                 | MySQL 主机（默认 localhost）    | -                                                          |
| Flask          | `SECRET_KEY`                 | Flask 密钥（自动生成也可）       | -                                                          |
| Redis          | `REDIS_URL`                  | Redis 连接地址                  | -                                                          |
| GitHub OAuth   | `GITHUB_CLIENT_ID`           | GitHub OAuth App Client ID     | https://github.com/settings/developers                      |
| GitHub OAuth   | `GITHUB_CLIENT_SECRET`       | GitHub OAuth App Client Secret | 同上                                                       |
| 阿里云 OSS     | `OSS_ACCESS_KEY_ID`          | 阿里云 AccessKey ID            | https://ram.console.aliyun.com/manage/ak                    |
| 阿里云 OSS     | `OSS_ACCESS_KEY_SECRET`      | 阿里云 AccessKey Secret        | 同上                                                       |
| 阿里云 OSS     | `OSS_BUCKET_NAME`            | OSS Bucket 名称                | 同上                                                       |
| 阿里云 OSS     | `OSS_ENDPOINT`               | OSS 地域节点                   | 同上                                                       |
| 通义千问 AI    | `DASHSCOPE_API_KEY`          | DashScope API Key              | https://dashscope.console.aliyun.com/apiKey                 |
| 高德地图       | `GAODE_WEATHER_KEY`          | 高德地图 Web服务 API Key        | https://lbs.amap.com/api/webservice/summary                 |
| SMTP 邮件      | `SMTP_SENDER_EMAIL`          | 发件人 QQ 邮箱地址              | QQ邮箱 → 设置 → 账户 → POP3/SMTP 服务                       |
| SMTP 邮件      | `SMTP_AUTH_CODE`             | QQ邮箱 SMTP 授权码（非密码）     | 同上，开启服务后获取16位授权码                                |
| 支付宝         | `ALIPAY_APP_ID`              | 支付宝沙箱 App ID               | https://open.alipay.com/develop/sandbox/app                 |
| 支付宝         | `ALIPAY_APP_PRIVATE_KEY`     | 应用私钥（PEM 格式完整内容）      | 支付宝沙箱 → 密钥管理 → 应用私钥                              |
| 支付宝         | `ALIPAY_ALIPAY_PUBLIC_KEY`   | 支付宝公钥（PEM 格式完整内容）    | 支付宝沙箱 → 密钥管理 → 支付宝公钥                            |
| 支付宝         | `ALIPAY_GATEWAY`             | 网关（沙箱默认即可）             | -                                                          |

**支付宝密钥的两种配置方式**:

1. **环境变量（推荐生产环境）**: 设置 `ALIPAY_APP_PRIVATE_KEY` 和 `ALIPAY_ALIPAY_PUBLIC_KEY` 为密钥的完整 PEM 内容
2. **本地文件（开发环境兼容）**: 将 `app_private_key.txt` 和 `alipay_public_key.txt` 放入 `exts/` 目录（这两个文件已在 `.gitignore` 中排除）

**`.env` 文件示例**:

```bash
# 创建 .env 文件在项目根目录
SECRET_KEY=your-secret-key-here
MYSQL_USER=root
MYSQL_PASSWORD=your-password
SMTP_SENDER_EMAIL=your-email@qq.com
SMTP_AUTH_CODE=your-16-char-code
DASHSCOPE_API_KEY=sk-your-key
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret
ALIPAY_APP_ID=2021000148684222
ALIPAY_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
ALIPAY_ALIPAY_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
```

### 4. 初始化数据库

```bash
# 先创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS flaskhousesystem DEFAULT CHARSET utf8mb4;"

# 导入初始 SQL（如果项目提供了 flaskhousesystem.sql）
mysql -u root -p flaskhousesystem < flaskhousesystem.sql
```

### 5. 启动 Redis

```bash
# 使用 Docker
docker run -d -p 6379:6379 redis:latest

# 或使用本地安装的 Redis
redis-server
```

### 6. 启动 Celery Worker（可选，用于异步邮件发送）

```bash
# 在项目根目录下
celery -A app.celery worker --loglevel=info -P threads
```

### 7. 运行项目

```bash
python app.py
# 服务启动在 http://localhost:5000
```

### 使用 Docker Compose 一键部署

```bash
docker-compose up -d
# 这会同时启动 MySQL、Redis 和 Flask 应用
```

---

## API 文档

> 所有接口统一返回格式：
> ```json
> {
>   "code": 200,
>   "success": true,
>   "message": "操作成功",
>   "data": {"...": "..."}
> }
> ```

### 一、用户模块 `/user`

| 方法   | 路径                       | 说明                         | 认证 |
| ------ | -------------------------- | ---------------------------- | ---- |
| POST   | `/user/register`           | 手机号注册                    | 否   |
| POST   | `/user/login`              | 手机号+密码登录                | 否   |
| POST   | `/user/email-login`        | 邮箱+密码登录                  | 否   |
| GET    | `/user/userinfo`           | 获取当前登录用户信息            | 是   |
| GET    | `/user/userinfo/<name>`    | 根据用户名查询用户              | 否   |
| PUT    | `/user/userinfo`           | 更新用户资料                   | 否   |
| PUT    | `/user/userinfo/password`  | 根据用户ID修改密码              | 否   |
| POST   | `/user/userinfo/password`  | 发送密码重置邮箱验证码          | 否   |
| PUT    | `/user/userinfo/password_e`| 根据邮箱修改密码                | 否   |
| GET    | `/user/userinfo/phone`     | 根据手机号查询用户              | 是   |
| POST   | `/user/userinfo/tolanlord` | 发送申请成为房东的邮箱验证码     | 否   |
| PUT    | `/user/userinfo/usertype`  | 升级用户为房东                  | 否   |
| GET    | `/user/userinfo/avatar`    | 获取用户头像URL                | 否   |
| POST   | `/user/userinfo/avatarurl` | 上传用户头像                    | 否   |

#### 注册 - `POST /user/register`

**请求** (`application/x-www-form-urlencoded`):

```
phone=13800138000&password=123456&email=user@example.com
```

**成功响应** (201):
```json
{
  "code": 201,
  "success": true,
  "message": "注册成功！"
}
```

#### 登录 - `POST /user/login`

**请求** (`application/x-www-form-urlencoded`):

```
phone=13800138000&password=123456
```

**成功响应** (201):
```json
{
  "code": 201,
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

#### 获取当前用户信息 - `GET /user/userinfo`

**请求头**: `Authorization: Bearer <token>`

**成功响应** (200):
```json
{
  "code": 200,
  "success": true,
  "message": "获取用户信息成功",
  "data": {
    "id": 1,
    "name": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "addr": null,
    "identityCard": null,
    "userType": 1,
    "avatarUrl": null
  }
}
```

#### 邮箱验证码登录 - `POST /email-auth/verify-login`

**请求** (JSON):
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**成功响应** (201):
```json
{
  "code": 201,
  "success": true,
  "message": "邮箱验证登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

---

### 二、房源信息模块 `/houseinfo`

| 方法   | 路径                              | 说明                         | 认证 |
| ------ | --------------------------------- | ---------------------------- | ---- |
| GET    | `/houseinfo/`                     | 获取房源列表（支持多条件筛选+分页） | 否   |
| GET    | `/houseinfo/<id>`                 | 获取单个房源详情               | 否   |
| POST   | `/houseinfo/`                     | 发布新房源                     | 否   |
| PUT    | `/houseinfo/<id>`                 | 更新房源信息                   | 否   |
| DELETE | `/houseinfo/<id>`                 | 删除房源                       | 否   |
| GET    | `/houseinfo/houseNums`             | 获取房源总数                   | 否   |
| GET    | `/houseinfo/hotLists`              | 获取热门房源（浏览量Top4）       | 否   |
| GET    | `/houseinfo/newLists`              | 获取最新房源（最新4条）          | 否   |
| GET    | `/houseinfo/piedata`               | 户型分布统计（饼图）            | 否   |
| GET    | `/houseinfo/columndata`            | 各小区房源数量Top20（柱状图）    | 否   |
| GET    | `/houseinfo/views`                 | 获取浏览量最高的房源            | 否   |
| POST   | `/houseinfo/views`                 | 增加房源浏览次数               | 否   |
| POST   | `/houseinfo/landlord`              | 根据房东用户名查询名下房源       | 否   |

#### 获取房源列表 - `GET /houseinfo/`

**查询参数**:

| 参数         | 类型    | 说明                                          |
| ------------ | ------- | --------------------------------------------- |
| `page`       | int     | 页码，默认 1                                   |
| `per_page`   | int     | 每页条数，默认 10                              |
| `region`     | string  | 区域，支持逗号分隔多选，如 `雨花,岳麓`           |
| `block`      | string  | 版块/街道                                      |
| `community`  | string  | 小区名（模糊搜索）                              |
| `rooms`      | string  | 户型，支持中文多选，如 `一居,两居,三居,四居+`     |
| `orientation`| string  | 朝向，支持逗号分隔多选，如 `南,南北`              |
| `min_price`  | int     | 最低租金（元/月）                               |
| `max_price`  | int     | 最高租金（元/月）                               |
| `rent_type`  | string  | 租赁类型：`整租` / `合租`                       |
| `subway`     | int     | 是否近地铁：`1`=是, `0`=否                     |
| `decoration` | string  | 装修情况：`精装`/`简装`/`毛坯`                  |
| `available`  | int     | 是否上架：`1`=是, `0`=否                       |

**示例**: `GET /houseinfo/?page=1&per_page=10&region=岳麓&min_price=1000&max_price=3000&rent_type=整租`

**成功响应** (200):
```json
{
  "code": 200,
  "success": true,
  "message": "查询成功",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "精装两室一厅近地铁",
        "region": "岳麓区",
        "community": "万科金域国际",
        "rooms": "2室1厅",
        "area": 85,
        "price": 2500,
        "rent_type": "整租",
        "direction": "南北",
        "subway": 1,
        "decoration": "精装",
        "publish_time": "2025-06-01",
        "image_url": "https://example.com/img.jpg",
        "features": ["近地铁", "拎包入住"],
        "tag_new": 1,
        "page_views": 328
      }
    ],
    "total": 156,
    "page": 1,
    "per_page": 10,
    "pages": 16
  }
}
```

---

### 三、房源详情模块 `/housedetail`

| 方法 | 路径                       | 说明                         | 认证 |
| ---- | -------------------------- | ---------------------------- | ---- |
| GET  | `/housedetail/<house_id>`   | 获取房源详情（图片/设施/地图）   | 否   |
| POST | `/housedetail/`            | 为已有房源添加详细信息          | 否   |

#### 获取房源详情 - `GET /housedetail/<house_id>`

**成功响应** (200):
```json
{
  "code": 200,
  "success": true,
  "data": {
    "id": 1,
    "house_info_id": 1,
    "photos": ["url1", "url2"],
    "facilities": {
      "wifi": true,
      "aircon": true,
      "washer": false
    },
    "map_coordinates": {
      "lat": 28.2282,
      "lng": 112.9388
    }
  }
}
```

---

### 四、评论模块 `/comments`

| 方法 | 路径                     | 说明               | 认证 |
| ---- | ------------------------ | ------------------ | ---- |
| GET  | `/comments/<house_id>`   | 获取房源下的评论     | 否   |
| POST | `/comments`              | 添加新评论          | 否   |

---

### 五、合同模块 `/contracts`

| 方法 | 路径                                           | 说明                          | 认证 |
| ---- | ---------------------------------------------- | ----------------------------- | ---- |
| POST | `/contracts`                                   | 创建合同（同时创建租房记录）      | 否   |
| GET  | `/contracts/<tenantName>/<landlord_id>`         | 根据租客姓名和房东ID查询合同     | 否   |

---

### 六、预约模块 `/appointments`

| 方法 | 路径             | 说明         | 认证 |
| ---- | ---------------- | ------------ | ---- |
| POST | `/appointments`  | 创建看房预约  | 否   |

---

### 七、维修投诉模块 `/repaires`

| 方法 | 路径                      | 说明                       | 认证 |
| ---- | ------------------------- | -------------------------- | ---- |
| POST | `/repaires`               | 提交维修申报或投诉            | 否   |
| GET  | `/repaires/complaint-persons` | 获取可投诉对象列表（所有房东） | 否   |

---

### 八、即时通讯模块 `/messages`

**REST 接口**:

| 方法 | 路径                                        | 说明                     | 认证 |
| ---- | ------------------------------------------- | ------------------------ | ---- |
| GET  | `/messages`                                 | 查询消息（支持多种筛选）     | 否   |
| POST | `/messages`                                 | 发送消息（REST 备用通道）   | 是   |
| GET  | `/messages/<sender>`                        | 查询某发送者的消息          | 否   |
| GET  | `/messages/receiver/<receiver>`              | 查询某接收者的消息          | 否   |

**Socket.IO 事件** (连接地址: `http://localhost:5000`):

| 事件名        | 方向         | 说明             |
| ------------- | ------------ | ---------------- |
| `authenticate` | 客户端→服务端 | 发送 token 认证   |
| `join_chat`    | 客户端→服务端 | 加入聊天房间       |
| `leave_chat`   | 客户端→服务端 | 离开聊天房间       |
| `send_message` | 客户端→服务端 | 发送实时消息       |
| `new_message`  | 服务端→客户端 | 收到新消息推送     |

---

### 九、新闻模块 `/news`

| 方法   | 路径          | 说明           | 认证 |
| ------ | ------------- | -------------- | ---- |
| GET    | `/news`       | 获取新闻列表（分页） | 否   |
| GET    | `/news/<id>`  | 获取新闻详情     | 否   |
| POST   | `/news`       | 创建新闻        | 否   |
| PUT    | `/news/<id>`  | 更新新闻        | 否   |
| DELETE | `/news/<id>`  | 删除新闻        | 否   |

---

### 十、AI 智能选房模块 `/chat-ai`

| 方法 | 路径                              | 说明                     | 认证 |
| ---- | --------------------------------- | ------------------------ | ---- |
| POST | `/chat-ai/chat`                   | AI 对话（非流式）          | 是   |
| POST | `/chat-ai/chat/stream`            | AI 流式对话（SSE）         | 是   |
| GET  | `/chat-ai/sessions`               | 获取用户的对话会话列表      | 是   |
| GET  | `/chat-ai/sessions/<id>/messages` | 获取会话的消息历史          | 否   |
| POST | `/chat-ai/houses/search`          | 直接搜索房源（不经过AI）    | 否   |
| GET  | `/chat-ai/houses/<id>`            | 获取单个房源详情            | 否   |
| GET  | `/chat-ai/houses/popular`         | 获取热门房源               | 否   |

#### AI 流式对话 - `POST /chat-ai/chat/stream`

**请求头**: `Authorization: Bearer <token>`

**请求** (JSON):
```json
{
  "message": "帮我推荐岳麓区2000元以内的两室一厅",
  "session_id": null
}
```

**响应**: Server-Sent Events (SSE) 流
```
data: {"type": "chunk", "content": "好的，我来"}
data: {"type": "chunk", "content": "帮您搜索..."}
data: {"type": "done", "session_id": 42}
```

---

### 十一、支付宝支付模块 `/api/alipay`

| 方法 | 路径                    | 说明                     | 认证 |
| ---- | ----------------------- | ------------------------ | ---- |
| POST | `/api/alipay/pay`       | 生成支付链接              | 否   |
| POST | `/api/alipay/notify`    | 支付宝异步回调（服务端）    | 否   |
| GET  | `/api/alipay/return`    | 支付完成同步回跳           | 否   |

---

### 十二、GitHub OAuth 模块 `/github`

| 方法 | 路径                 | 说明                         | 认证 |
| ---- | -------------------- | ---------------------------- | ---- |
| GET  | `/github/login`      | 跳转 GitHub 授权页面           | 否   |
| GET  | `/github/callback`   | GitHub 授权回调，签发 JWT token | 否   |

---

### 十三、邮箱验证码模块 `/email-auth`

| 方法 | 路径                       | 说明                 | 认证 |
| ---- | -------------------------- | -------------------- | ---- |
| POST | `/email-auth/send-code`     | 发送邮箱验证码         | 否   |
| POST | `/email-auth/verify-login`   | 验证码登录            | 否   |
| POST | `/email-auth/verify-code`    | 仅验证验证码（不登录）  | 否   |

---

### 十四、系统日志模块 `/admin/logs`

| 方法 | 路径                | 说明                    | 认证 |
| ---- | ------------------- | ----------------------- | ---- |
| GET  | `/admin/logs/`       | 获取日志列表（支持筛选+分页） | 否   |
| POST | `/admin/logs/delete` | 批量删除日志              | 否   |
| GET  | `/admin/logs/levels` | 获取日志级别分布统计       | 否   |

---

### 十五、租房记录模块 `/rental`

| 方法 | 路径                                 | 说明                       | 认证 |
| ---- | ------------------------------------ | -------------------------- | ---- |
| GET  | `/rental/tenants/<tenant_username>`  | 获取租客的所有租房记录        | 否   |

---

## 认证说明

- JWT Token 有效期 **24 小时**
- 登录后需在请求头携带: `Authorization: Bearer <token>`
- 标记"认证：是"的接口需要携带有效 token
- Socket.IO 连接需先发送 `authenticate` 事件进行认证

## 环境变量

通过 `.env` 文件或 Docker 环境变量可覆盖 `config.py` 中的默认值：

| 变量名                      | 说明                      |
| --------------------------- | ------------------------- |
| `MYSQL_USER`                | 数据库用户名               |
| `MYSQL_PASSWORD`            | 数据库密码                 |
| `MYSQL_HOST`                | 数据库主机                 |
| `MYSQL_PORT`                | 数据库端口                 |
| `MYSQL_DB`                  | 数据库名称                 |
| `SECRET_KEY`                | Flask Secret Key          |
| `REDIS_URL`                 | Redis 连接地址             |
| `GITHUB_CLIENT_ID`          | GitHub OAuth Client ID    |
| `GITHUB_CLIENT_SECRET`      | GitHub OAuth Secret       |
| `DASHSCOPE_API_KEY`         | 通义千问 API Key           |
| `GAODE_WEATHER_KEY`         | 高德地图 API Key           |
| `OSS_ACCESS_KEY_ID`         | 阿里云 OSS AccessKey      |
| `OSS_ACCESS_KEY_SECRET`     | 阿里云 OSS Secret         |
| `SMTP_SENDER_EMAIL`         | QQ邮箱发件人地址           |
| `SMTP_AUTH_CODE`            | QQ邮箱 SMTP 授权码         |
| `ALIPAY_APP_ID`             | 支付宝沙箱 App ID          |
| `ALIPAY_APP_PRIVATE_KEY`    | 支付宝应用私钥（PEM内容）   |
| `ALIPAY_ALIPAY_PUBLIC_KEY`  | 支付宝公钥（PEM内容）       |

## Docker 部署

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f app

# 停止
docker-compose down
```

MySQL 数据通过 volume `mysql_data` 持久化，Redis 数据通过 volume `redis_data` 持久化。
