#!/bin/bash
# Sehuatang 爬虫系统启动脚本
# 重构版 - 简化启动流程

set -e

echo "🚀 启动 Sehuatang 爬虫系统..."

# 设置时区
export TZ=Asia/Shanghai

# 等待数据库启动
echo "⏳ 等待数据库连接..."
sleep 5

# 进入后端目录
cd /app/backend

# 启动服务
echo "📡 启动后端服务..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 &

# 启动前端
echo "🎨 启动前端服务..."
cd /app/frontend
serve -s build -l 3000 &

echo "✅ 启动完成！"
echo "📡 后端API: http://localhost:8000"
echo "🎨 前端界面: http://localhost:3000"
echo "📊 API文档: http://localhost:8000/docs"

# 保持运行
wait
