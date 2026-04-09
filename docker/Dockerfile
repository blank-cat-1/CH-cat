FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 全局安装serve
RUN npm install -g serve

# 复制应用代码
COPY backend/ ./backend/
COPY frontend/build/ ./frontend/build/
COPY scripts/ ./scripts/

# 创建数据目录
RUN mkdir -p /app/data/cookies /app/data/logs /app/logs

# 暴露端口
EXPOSE 8000 3000

# 启动脚本
CMD ["/bin/bash", "/app/scripts/start.sh"]
