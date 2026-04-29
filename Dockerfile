# 1. 使用你指定的 Python 3.13.2 轻量级镜像
FROM python:3.13-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. 安装必要的系统构建依赖
# 注意：Python 3.13 较新，确保安装基本的 C 编译器以适配 bcrypt 等库
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. 复制项目所有代码
COPY . .

# 7. 暴露端口（Flask 应用端口）
EXPOSE 5000

# 8. 启动命令
CMD ["python", "app.py"]