#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
磁力链接路由
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from core import get_db
from models import MagnetLink

router = APIRouter()


class MagnetResponse(BaseModel):
    id: int
    title: str
    url: str
    magnets: Optional[str] = None
    code: Optional[str] = None
    author: Optional[str] = None
    forum_type: Optional[str] = None
    size: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[MagnetResponse])
async def list_magnets(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    forum_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取磁力链接列表"""
    query = db.query(MagnetLink)
    
    if search:
        query = query.filter(MagnetLink.title.ilike(f"%{search}%"))
    
    if forum_type:
        query = query.filter(MagnetLink.forum_type == forum_type)
    
    magnets = query.order_by(MagnetLink.created_at.desc()).offset(skip).limit(limit).all()
    return magnets


@router.get("/{magnet_id}")
async def get_magnet(magnet_id: int, db: Session = Depends(get_db)):
    """获取磁力链接详情"""
    magnet = db.query(MagnetLink).filter(MagnetLink.id == magnet_id).first()
    
    if not magnet:
        return {"error": "磁力链接不存在"}
    
    return magnet.to_dict()


@router.delete("/{magnet_id}")
async def delete_magnet(magnet_id: int, db: Session = Depends(get_db)):
    """删除磁力链接"""
    magnet = db.query(MagnetLink).filter(MagnetLink.id == magnet_id).first()
    
    if not magnet:
        return {"error": "磁力链接不存在"}
    
    db.delete(magnet)
    db.commit()
    
    return {"message": "删除成功"}
