#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sehuatang 爬虫系统 - 主应用入口
重构版本
"""

import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 初始化日志
from core import setup_logging, settings
setup_logging()
logger = logging.getLogger("sehuatang")

# 禁用SQLAlchemy详细日志
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

# 导入路由
from api.routes import (
    auth_router,
    subscription_router,
    crawler_router,
    magnet_router,
    search_router,
    settings_router,
    emby_router,
    telegram_router,
    notification_router,
    health_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 Sehuatang 爬虫系统启动中...")
    
    # 1. 初始化数据库
    try:
        from core import init_database
        init_database()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
    
    # 2. 初始化定时任务调度器
    try:
        from core.scheduler import init_scheduler, start_scheduler
        init_scheduler()
        start_scheduler()
        logger.info("✅ 定时任务调度器启动完成")
    except Exception as e:
        logger.warning(f"⚠️ 定时任务调度器启动失败: {e}")
    
    # 3. 初始化Cookie自动检查器
    try:
        from services.notification import CookieAutoChecker
        checker = CookieAutoChecker()
        checker.start()
        logger.info("✅ Cookie自动检查器启动完成")
    except Exception as e:
        logger.warning(f"⚠️ Cookie自动检查器启动失败: {e}")
    
    logger.info("🚀 Sehuatang 爬虫系统启动成功！")
    
    yield
    
    # 关闭时清理
    logger.info("👋 Sehuatang 爬虫系统关闭中...")
    try:
        from core.scheduler import stop_scheduler
        stop_scheduler()
    except:
        pass
    logger.info("👋 Sehuatang 爬虫系统已关闭")


# 创建应用
app = FastAPI(
    title="Sehuatang 爬虫系统",
    description="论坛爬虫、订阅管理、Telegram通知、Emby集成",
    version="2.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(subscription_router, prefix="/api/subscriptions", tags=["订阅管理"])
app.include_router(crawler_router, prefix="/api/crawler", tags=["爬虫管理"])
app.include_router(magnet_router, prefix="/api/magnets", tags=["磁力链接"])
app.include_router(search_router, prefix="/api/search", tags=["搜索"])
app.include_router(settings_router, prefix="/api/settings", tags=["设置"])
app.include_router(emby_router, prefix="/api/emby", tags=["Emby"])
app.include_router(telegram_router, prefix="/api/telegram", tags=["Telegram"])
app.include_router(notification_router, prefix="/api/notifications", tags=["通知"])
app.include_router(health_router, tags=["健康检查"])


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    from datetime import datetime
    from core import check_db_health
    
    db_healthy = check_db_health()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "database": "connected" if db_healthy else "disconnected"
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Sehuatang 爬虫系统",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower()
    )
