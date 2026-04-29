# 1. 使用官方 Python 轻量级镜像作为基础
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 设置环境变量，确保 Python 输出直接打印到终端，不进行缓冲
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. 安装系统依赖（如果某些 Python 库需要 C 编译环境）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 复制项目所有代码到镜像中
COPY . .

# 7. 暴露 Flask 运行的端口（根据你的 app.py，默认通常是 5000）
EXPOSE 5000

# 8. 启动命令（这里使用 socketio.run 对应的启动方式）
CMD ["python", "app.py"]