#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索路由
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from core import get_db
from models import Post

router = APIRouter()


class PostResponse(BaseModel):
    id: int
    tid: str
    title: str
    author: Optional[str] = None
    board_name: Optional[str] = None
    magnet_link: Optional[str] = None
    preview_image: Optional[str] = None
    published_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[PostResponse])
async def search_posts(
    q: str = Query(..., description="搜索关键词"),
    skip: int = 0,
    limit: int = 50,
    author: Optional[str] = None,
    board: Optional[str] = None,
    has_magnet: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """搜索帖子"""
    query = db.query(Post).filter(
        Post.title.ilike(f"%{q}%") | Post.content.ilike(f"%{q}%")
    )
    
    if author:
        query = query.filter(Post.author.ilike(f"%{author}%"))
    
    if board:
        query = query.filter(Post.board_name.ilike(f"%{board}%"))
    
    if has_magnet is True:
        query = query.filter(Post.magnet_link.isnot(None))
        query = query.filter(Post.magnet_link != "")
    
    posts = query.order_by(Post.published_at.desc()).offset(skip).limit(limit).all()
    return posts


@router.get("/count")
async def count_posts(
    q: str = Query(..., description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """统计搜索结果数量"""
    count = db.query(Post).filter(
        Post.title.ilike(f"%{q}%") | Post.content.ilike(f"%{q}%")
    ).count()
    
    return {"count": count}
