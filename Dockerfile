# ============================================================
# 链居 - 后端 Dockerfile
# Python Flask + SQLAlchemy + Celery
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
    && rm -rf /var/lib/apt/lists/*

# 利用 Docker 缓存：先复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

EXPOSE 5000

CMD ["python", "app.py"]
