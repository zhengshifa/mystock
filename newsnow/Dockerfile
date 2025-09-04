# 使用官方 Python 3.11 slim 镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_SYSTEM_PYTHON=1

# 替换为阿里云 Debian 源（适配 python:3.11-slim）
RUN echo "deb https://mirrors.aliyun.com/debian trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian-security trixie-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian trixie-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
       curl wget ca-certificates gcc g++ libxml2-dev libxslt1-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 安装 uv 包管理器
RUN pip install --no-cache-dir uv==0.4.0

# 创建非 root 用户
RUN groupadd --gid 1000 newsnow && \
    useradd --uid 1000 --gid newsnow --shell /bin/bash --create-home newsnow

# 复制项目配置文件
COPY pyproject.toml uv.lock ./

# 创建虚拟环境并安装依赖
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install --system -r pyproject.toml

# 复制源代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs config && \
    chown -R newsnow:newsnow /app

# 切换到非 root 用户
USER newsnow

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    LOG_LEVEL="INFO" \
    LOG_FILE="logs/newsnow.log" \
    MONGODB_HOST="mongodb" \
    MONGODB_PORT="27017" \
    MONGODB_DATABASE="newsnow" \
    FETCH_INTERVAL="300" \
    MAX_CONCURRENT_SOURCES="10" \
    REQUEST_TIMEOUT="30" \
    MAX_RETRIES="3"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import asyncio; from database.mongodb import get_mongodb_connection; conn = get_mongodb_connection(); exit(0 if conn and asyncio.run(conn.health_check()) else 1)" || exit 1

# 暴露端口（如果需要API服务）
# EXPOSE 8000

# 创建启动脚本
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# 等待MongoDB启动\n\
echo "等待MongoDB启动..."\n\
while ! python -c "import asyncio; from database.mongodb import init_mongodb; asyncio.run(init_mongodb())" 2>/dev/null; do\n\
    echo "MongoDB未就绪，等待5秒..."\n\
    sleep 5\n\
done\n\
echo "MongoDB已就绪"\n\
\n\
# 启动应用\n\
exec "$@"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"]

# 默认启动命令
CMD ["python", "main.py"]