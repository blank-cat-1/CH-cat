#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅管理路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from core import get_db
from models import Subscription

router = APIRouter()


# Pydantic模型
class SubscriptionBase(BaseModel):
    name: str
    description: Optional[str] = None
    subscription_type: str = "forum"
    fid: Optional[str] = None
    keywords: Optional[str] = None
    include_keywords: Optional[str] = None
    exclude_keywords: Optional[str] = None
    page_start: int = 1
    page_end: int = 10
    phase: str = "watch"
    enabled: bool = True


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(SubscriptionBase):
    pass


class SubscriptionResponse(SubscriptionBase):
    id: int
    is_active: bool
    last_run_at: Optional[str] = None
    total_runs: int = 0
    total_posts: int = 0

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    skip: int = 0,
    limit: int = 100,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取订阅列表"""
    query = db.query(Subscription)
    
    if enabled is not None:
        query = query.filter(Subscription.enabled == enabled)
    
    subscriptions = query.offset(skip).limit(limit).all()
    return subscriptions


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """获取单个订阅"""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    return subscription


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    """创建订阅"""
    db_subscription = Subscription(**subscription.model_dump())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    
    return db_subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    subscription: SubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """更新订阅"""
    db_subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    if not db_subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    for key, value in subscription.model_dump().items():
        setattr(db_subscription, key, value)
    
    db.commit()
    db.refresh(db_subscription)
    
    return db_subscription


@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """删除订阅"""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    db.delete(subscription)
    db.commit()
    
    return {"message": "订阅已删除"}


@router.post("/{subscription_id}/run")
async def run_subscription_now(subscription_id: int, db: Session = Depends(get_db)):
    """立即运行订阅"""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    # 触发爬虫
    from services.crawler.engine import run_subscription
    import asyncio
    
    try:
        new_posts = asyncio.get_event_loop().run_until_complete(
            run_subscription(subscription_id, trigger_type='manual')
        )
        
        # 更新统计
        subscription.total_runs += 1
        subscription.total_posts += new_posts
        db.commit()
        
        return {
            "message": "订阅执行完成",
            "new_posts": new_posts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.post("/{subscription_id}/toggle")
async def toggle_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """切换订阅启用状态"""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    subscription.enabled = not subscription.enabled
    subscription.is_active = subscription.enabled
    db.commit()
    
    return {
        "message": "切换成功",
        "enabled": subscription.enabled
    }
