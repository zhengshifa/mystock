# 使用官方 Python 3.11 slim 镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml requirements.txt ./
COPY newsnow_py/ ./newsnow_py/

# 创建虚拟环境并安装依赖
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt

# 创建日志目录
RUN mkdir -p logs

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash newsnow && \
    chown -R newsnow:newsnow /app

# 切换到非 root 用户
USER newsnow

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from newsnow_py.database.mongodb import MongoDBConnection; asyncio.run(MongoDBConnection().health_check())" || exit 1

# 暴露端口（如果需要的话）
# EXPOSE 8000

# 启动命令
CMD ["python", "-m", "newsnow_py"]