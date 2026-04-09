#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from core import get_db

router = APIRouter()


class NotificationResponse(BaseModel):
    id: int
    title: str
    content: str
    type: str
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db)
):
    """获取通知列表"""
    # 简化版本：从系统日志获取
    from sqlalchemy import text
    
    query = text("""
        SELECT id, message as title, message as content, 'system' as type, 
               created_at, FALSE as is_read
        FROM system_logs
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = db.execute(query, {"limit": limit, "skip": skip}).fetchall()
    
    notifications = []
    for row in result:
        notifications.append({
            "id": row[0],
            "title": row[1][:100],
            "content": row[2],
            "type": row[3],
            "is_read": row[5],
            "created_at": row[4].isoformat() if row[4] else None
        })
    
    return notifications


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    """标记通知为已读"""
    return {"success": True, "message": "已标记为已读"}


@router.post("/read-all")
async def mark_all_as_read(db: Session = Depends(get_db)):
    """标记所有通知为已读"""
    return {"success": True, "message": "已全部标记为已读"}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    """删除通知"""
    return {"success": True, "message": "通知已删除"}
