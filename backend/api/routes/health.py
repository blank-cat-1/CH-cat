#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查路由
"""

from fastapi import APIRouter
from datetime import datetime
from core import check_db_health

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    db_healthy = check_db_health()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "database": "connected" if db_healthy else "disconnected",
        "components": {
            "database": "ok" if db_healthy else "error",
            "scheduler": "ok",
            "crawler": "ok"
        }
    }


@router.get("/")
async def root():
    """系统信息"""
    return {
        "name": "Sehuatang 爬虫系统",
        "version": "2.0.0",
        "description": "论坛爬虫、订阅管理、通知推送"
    }
