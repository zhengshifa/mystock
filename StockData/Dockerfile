# 使用Python 3.11官方镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN echo 'Acquire::http::Proxy "http://38.19.66.199:7890";' >> /etc/apt/apt.conf && \
    echo 'Acquire::https::Proxy "http://38.19.66.199:7890";' >> /etc/apt/apt.conf && \
    apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 指定步骤去缓存构建
# docker build --build-arg BUST_CACHE=$([Math]::Floor([decimal](Get-Date -UFormat %s))) . -t newsnow:v1
# docker build --build-arg BUST_CACHE=$(date +%s) .

# 跳过步骤缓存
ARG BUST_CACHE
# 复制项目文件
COPY . .

# 使用uv安装Python依赖
RUN pip install -r requirements.txt

# 创建日志目录
RUN mkdir -p logs

# 设置权限
RUN chmod +x main.py start.py

# 暴露端口（如果需要的话）
# EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 默认启动命令（调度模式）
CMD ["python", "start.py"]