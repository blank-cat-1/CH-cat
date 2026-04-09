#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, Any

from core import get_db

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: Any


@router.get("/")
async def get_settings(db: Session = Depends(get_db)):
    """获取所有设置"""
    try:
        result = db.execute(text("SELECT key, value FROM settings")).fetchall()
        settings = {row[0]: row[1] for row in result}
        return settings
    except:
        return {}


@router.get("/{key}")
async def get_setting(key: str, db: Session = Depends(get_db)):
    """获取单个设置"""
    try:
        result = db.execute(
            text("SELECT value FROM settings WHERE key = :key"),
            {"key": key}
        ).fetchone()
        
        if result:
            return {"key": key, "value": result[0]}
        return {"key": key, "value": None}
    except:
        return {"key": key, "value": None}


@router.post("/")
async def update_setting(setting: SettingUpdate, db: Session = Depends(get_db)):
    """更新设置"""
    try:
        db.execute(
            text("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (:key, :value, NOW())
                ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
            """),
            {"key": setting.key, "value": str(setting.value)}
        )
        db.commit()
        return {"success": True, "message": "设置已更新"}
    except Exception as e:
        return {"success": False, "message": str(e)}
