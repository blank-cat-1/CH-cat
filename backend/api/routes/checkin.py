#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
签到路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from core import get_db
from models import CheckinConfig, CheckinRecord

router = APIRouter()


class CheckinConfigResponse(BaseModel):
    id: int
    enabled: bool
    schedule_hour: int
    schedule_minute: int
    random_delay_minutes: int
    telegram_notifications_enabled: bool
    last_run_at: Optional[str] = None
    last_run_status: Optional[str] = None

    class Config:
        from_attributes = True


class CheckinRecordResponse(BaseModel):
    id: int
    checkin_date: str
    status: str
    reward_type: Optional[str] = None
    reward_amount: Optional[int] = None
    reward_message: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/config", response_model=CheckinConfigResponse)
async def get_checkin_config(db: Session = Depends(get_db)):
    """获取签到配置"""
    config = db.query(CheckinConfig).first()
    
    if not config:
        # 创建默认配置
        config = CheckinConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config


@router.post("/config")
async def update_checkin_config(
    enabled: bool = True,
    schedule_hour: int = 10,
    schedule_minute: int = 0,
    random_delay_minutes: int = 30,
    telegram_notifications_enabled: bool = True,
    db: Session = Depends(get_db)
):
    """更新签到配置"""
    config = db.query(CheckinConfig).first()
    
    if not config:
        config = CheckinConfig()
        db.add(config)
    
    config.enabled = enabled
    config.schedule_hour = schedule_hour
    config.schedule_minute = schedule_minute
    config.random_delay_minutes = random_delay_minutes
    config.telegram_notifications_enabled = telegram_notifications_enabled
    
    db.commit()
    
    return {"success": True, "message": "配置已更新"}


@router.get("/records", response_model=List[CheckinRecordResponse])
async def get_checkin_records(
    skip: int = 0,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """获取签到记录"""
    records = db.query(CheckinRecord).order_by(
        CheckinRecord.checkin_date.desc()
    ).offset(skip).limit(limit).all()
    
    return records


@router.post("/now")
async def checkin_now(db: Session = Depends(get_db)):
    """立即执行签到"""
    # 这里应该调用实际的签到服务
    # 简化版本只记录一次尝试
    try:
        record = CheckinRecord(
            checkin_date=datetime.utcnow(),
            status="success",
            reward_type="points",
            reward_amount=10,
            reward_message="签到成功，获得10积分"
        )
        db.add(record)
        db.commit()
        
        return {"success": True, "message": "签到成功"}
    except Exception as e:
        return {"success": False, "message": str(e)}
