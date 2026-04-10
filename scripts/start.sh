#!/bin/bash
# Sehuatang 爬虫系统启动脚本
# 重构版 - 统一端口（前端+API）

set -e

echo "🚀 启动 Sehuatang 爬虫系统..."

# 设置时区
export TZ=Asia/Shanghai

# 等待数据库启动
echo "⏳ 等待数据库连接..."
sleep 5

# 进入后端目录（后端同时服务前端静态文件）
cd /app/backend

# 启动服务（统一 8900 端口）
echo "📡 启动服务（前端+API）..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

echo "✅ 启动完成！"
echo "🌐 统一入口: http://localhost:8000"
echo "📊 API文档: http://localhost:8000/docs"
