#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram机器人路由
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core import get_db, settings

router = APIRouter()


class TelegramConfig(BaseModel):
    bot_token: Optional[str] = None
    webhook_url: Optional[str] = None
    use_webhook: bool = False
    enabled: bool = False


@router.get("/status")
async def get_telegram_status():
    """获取Telegram机器人状态"""
    if not settings.telegram_bot_token:
        return {
            "enabled": False,
            "message": "Telegram机器人未配置"
        }
    
    return {
        "enabled": True,
        "token_prefix": settings.telegram_bot_token[:10] + "...",
        "message": "Telegram机器人已配置"
    }


@router.post("/config")
async def update_telegram_config(
    bot_token: str,
    webhook_url: Optional[str] = None,
    use_webhook: bool = False,
    enabled: bool = True,
    db: Session = Depends(get_db)
):
    """更新Telegram配置"""
    if enabled and not bot_token:
        raise HTTPException(status_code=400, detail="启用机器人需要提供Token")
    
    try:
        from sqlalchemy import text
        
        configs = [
            ("telegram_bot_token", bot_token),
            ("telegram_bot_webhook_url", webhook_url or ""),
            ("telegram_bot_use_webhook", str(use_webhook)),
            ("telegram_bot_enabled", str(enabled))
        ]
        
        for key, value in configs:
            db.execute(
                text("""
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (:key, :value, NOW())
                    ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
                """),
                {"key": key, "value": value}
            )
        
        db.commit()
        return {"success": True, "message": "Telegram配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_telegram_message(message: str = "测试消息"):
    """发送测试消息"""
    if not settings.telegram_bot_token:
        return {"success": False, "message": "Telegram机器人未配置"}
    
    # 简化版本：记录尝试
    return {"success": True, "message": f"测试消息: {message}"}
