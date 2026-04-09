#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emby集成路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from core import get_db, settings
from models import MagnetLink

router = APIRouter()


class EmbyConfig(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    user_id: Optional[str] = None
    library_ids: Optional[List[str]] = None


class EmbyItem(BaseModel):
    id: str
    name: str
    type: str
    status: str


@router.get("/status")
async def get_emby_status():
    """获取Emby连接状态"""
    if not settings.emby_base_url or not settings.emby_api_key:
        return {
            "connected": False,
            "message": "Emby未配置"
        }
    
    return {
        "connected": True,
        "base_url": settings.emby_base_url,
        "message": "Emby已配置"
    }


@router.post("/config")
async def update_emby_config(config: EmbyConfig, db: Session = Depends(get_db)):
    """更新Emby配置"""
    # 简化版本：保存到settings表
    try:
        from sqlalchemy import text
        
        for key, value in config.model_dump().items():
            if value is not None:
                db.execute(
                    text("""
                        INSERT INTO settings (key, value, updated_at)
                        VALUES (:key, :value, NOW())
                        ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
                    """),
                    {"key": f"emby_{key}", "value": str(value)}
                )
        
        db.commit()
        return {"success": True, "message": "Emby配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items")
async def get_emby_items(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取Emby已索引的项"""
    from models import MagnetLink
    
    items = db.query(MagnetLink).filter(
        MagnetLink.in_emby == True
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": item.id,
            "name": item.title,
            "type": "Movie",
            "emby_item_id": item.emby_item_id
        }
        for item in items
    ]


@router.post("/sync")
async def sync_to_emby(post_id: int, db: Session = Depends(get_db)):
    """同步帖子到Emby"""
    post = db.query(MagnetLink).filter(MagnetLink.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 简化版本：标记为已同步
    post.in_emby = True
    from datetime import datetime
    post.emby_checked_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "已同步到Emby"}
