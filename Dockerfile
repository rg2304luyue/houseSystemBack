# ============================================================
# 链居 - 后端 Dockerfile
# Python Flask + SQLAlchemy + Celery + Gunicorn
# ============================================================

FROM python:3.13-slim

WORKDIR /app

# 防止生成 .pyc 文件，确保日志实时输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统编译依赖（bcrypt 等需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 利用 Docker 缓存：先复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

EXPOSE 5000

# 生产环境使用 Gunicorn（可通过环境变量调整 workers 数量）
CMD gunicorn -w ${GUNICORN_WORKERS:-4} -b 0.0.0.0:5000 --timeout 120 app:app
