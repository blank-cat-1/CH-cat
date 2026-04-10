#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动签到API路由
"""

import logging
from datetime import date, timedelta, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth_deps import get_current_user
from models.user import User
from models.checkin import CheckInRecord, CheckInConfig
from services.auto_checkin_service import auto_checkin_service

logger = logging.getLogger(__name__)

router = APIRouter()


# === Pydantic 模型 ===

class CheckInConfigResponse(BaseModel):
    id: int
    enabled: bool
    target_board: str
    reply_count_per_day: int
    checkin_time: str
    random_delay_min: int
    random_delay_max: int
    retry_count: int
    notification_enabled: bool
    telegram_notifications_enabled: bool


class CheckInConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    target_board: Optional[str] = None
    reply_count_per_day: Optional[int] = Field(None, ge=1, le=10)
    checkin_time: Optional[str] = None
    random_delay_min: Optional[int] = Field(None, ge=0, le=300)
    random_delay_max: Optional[int] = Field(None, ge=30, le=600)
    retry_count: Optional[int] = Field(None, ge=1, le=10)
    notification_enabled: Optional[bool] = None
    telegram_notifications_enabled: Optional[bool] = None


class CheckInStatsResponse(BaseModel):
    total_checkins: int
    current_streak: int
    total_replies: int
    last_checkin: Optional[str] = None
    total_actual_points: int
    total_actual_money: int
    total_actual_coins: int
    today_gains: dict
    week_gains: dict
    month_gains: dict
    avg_points_per_day: float
    avg_money_per_day: float
    recent_records: List[dict]


class ManualCheckinResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# === API 接口 ===

@router.get("/config", response_model=CheckInConfigResponse)
async def get_checkin_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取签到配置"""
    try:
        config = db.query(CheckInConfig).first()
        if not config:
            config = CheckInConfig()
            db.add(config)
            db.commit()
            db.refresh(config)

        return CheckInConfigResponse(
            id=config.id,
            enabled=config.enabled,
            target_board=config.target_board,
            reply_count_per_day=config.reply_count_per_day,
            checkin_time=config.checkin_time,
            random_delay_min=config.random_delay_min,
            random_delay_max=config.random_delay_max,
            retry_count=config.retry_count,
            notification_enabled=config.notification_enabled,
            telegram_notifications_enabled=getattr(config, 'telegram_notifications_enabled', True)
        )

    except Exception as e:
        logger.error(f"获取签到配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取签到配置失败")


@router.put("/config")
async def update_checkin_config(
    config_data: CheckInConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新签到配置"""
    try:
        config = db.query(CheckInConfig).first()
        if not config:
            config = CheckInConfig()
            db.add(config)

        update_data = config_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        db.commit()
        db.refresh(config)

        logger.info(f"签到配置已更新: {update_data}")

        return {
            "success": True,
            "message": "签到配置更新成功",
            "data": {
                "id": config.id,
                "enabled": config.enabled,
                "target_board": config.target_board,
                "reply_count_per_day": config.reply_count_per_day,
                "checkin_time": config.checkin_time,
                "random_delay_min": config.random_delay_min,
                "random_delay_max": config.random_delay_max,
                "retry_count": config.retry_count,
                "notification_enabled": config.notification_enabled
            }
        }

    except Exception as e:
        logger.error(f"更新签到配置失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新签到配置失败: {str(e)}")


@router.get("/stats", response_model=CheckInStatsResponse)
async def get_checkin_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """获取签到统计"""
    try:
        stats = await auto_checkin_service.get_checkin_stats(days)
        return CheckInStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取签到统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取签到统计失败")


@router.post("/manual", response_model=ManualCheckinResponse)
async def manual_checkin(
    current_user: User = Depends(get_current_user)
):
    """手动执行签到"""
    try:
        logger.info("🎯 收到手动签到请求，开始立即执行")
        result = await auto_checkin_service.perform_daily_checkin(test_mode=False)
        logger.info(f"手动签到执行完成: {result}")

        return ManualCheckinResponse(
            success=result.get('success', False),
            message=result.get('message', '签到完成'),
            data=result.get('data')
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"手动签到失败: {error_msg}")
        raise HTTPException(status_code=500, detail=f"手动签到失败: {error_msg}")


@router.get("/records")
async def get_checkin_records(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取签到记录"""
    try:
        offset = (page - 1) * page_size

        records = db.query(CheckInRecord).order_by(
            CheckInRecord.checkin_date.desc()
        ).offset(offset).limit(page_size).all()

        total = db.query(CheckInRecord).count()

        return {
            "success": True,
            "data": [
                {
                    "id": record.id,
                    "checkin_date": record.checkin_date.isoformat(),
                    "status": record.status,
                    "reply_count": record.reply_count,
                    "reward_points": record.reward_points,
                    "reward_description": record.reward_description,
                    "error_message": record.error_message,
                    "execution_time": record.execution_time,
                    "actual_gains": {
                        "points": record.actual_points_gained or 0,
                        "money": record.actual_money_gained or 0,
                        "coins": record.actual_coins_gained or 0
                    },
                    "created_at": record.created_at.isoformat() if record.created_at else None
                }
                for record in records
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        }

    except Exception as e:
        logger.error(f"获取签到记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取签到记录失败")


@router.delete("/records/{record_id}")
async def delete_checkin_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除签到记录"""
    try:
        record = db.query(CheckInRecord).filter(CheckInRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="签到记录不存在")

        db.delete(record)
        db.commit()

        logger.info(f"删除签到记录: {record_id}")

        return {"success": True, "message": "签到记录删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除签到记录失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除签到记录失败: {str(e)}")


@router.get("/logs")
async def get_checkin_logs(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取签到系统日志"""
    try:
        from models.system_log import SystemLog

        offset = (page - 1) * limit

        query = db.query(SystemLog).filter(SystemLog.source == "checkin_system")
        logs = query.order_by(SystemLog.timestamp.desc()).offset(offset).limit(limit).all()
        total = query.count()

        return {
            "success": True,
            "data": {
                "logs": [
                    {
                        "id": log.id,
                        "level": log.level,
                        "message": log.message,
                        "operation": log.operation,
                        "details": log.details,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else None
                    }
                    for log in logs
                ],
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,
            }
        }

    except Exception as e:
        logger.error(f"获取签到日志失败: {e}")
        raise HTTPException(status_code=500, detail="获取签到日志失败")


@router.post("/run-now")
async def run_checkin_now(
    current_user: User = Depends(get_current_user)
):
    """立即执行签到任务"""
    try:
        logger.info("🎯 收到立即执行签到任务请求")
        result = await auto_checkin_service.perform_daily_checkin(test_mode=False)

        return {
            "success": result.get('success', False),
            "message": result.get('message', '签到任务执行完成'),
            "data": result.get('data', {})
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"立即执行签到任务失败: {error_msg}")
        raise HTTPException(status_code=500, detail=f"执行签到任务失败: {error_msg}")


@router.get("/task-info")
async def get_checkin_task_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取签到任务详细信息"""
    try:
        config = db.query(CheckInConfig).first()
        if not config:
            config = CheckInConfig()
            db.add(config)
            db.commit()
            db.refresh(config)

        recent_records = db.query(CheckInRecord).order_by(
            CheckInRecord.checkin_date.desc()
        ).limit(5).all()

        total_checkins = db.query(CheckInRecord).filter(
            CheckInRecord.status.in_(['success', 'test_success'])
        ).count()

        success_checkins = db.query(CheckInRecord).filter(
            CheckInRecord.status == 'success'
        ).count()

        success_rate = (success_checkins / total_checkins * 100) if total_checkins > 0 else 0

        return {
            "success": True,
            "data": {
                "task_info": {
                    "id": "daily_checkin",
                    "name": "每日自动签到",
                    "job_type": "auto_checkin",
                    "description": "自动签到任务，每日自动执行签到和回复帖子",
                    "enabled": config.enabled,
                    "status": "active",
                    "trigger_description": f"每天 {config.checkin_time} 执行"
                },
                "config": {
                    "enabled": config.enabled,
                    "target_board": config.target_board,
                    "reply_count_per_day": config.reply_count_per_day,
                    "checkin_time": config.checkin_time,
                    "random_delay_min": config.random_delay_min,
                    "random_delay_max": config.random_delay_max,
                },
                "statistics": {
                    "total_checkins": total_checkins,
                    "success_checkins": success_checkins,
                    "success_rate": round(success_rate, 1)
                },
                "recent_records": [
                    {
                        "date": record.checkin_date.isoformat(),
                        "status": record.status,
                        "reply_count": record.reply_count or 0,
                        "points_gained": record.actual_points_gained or 0,
                        "money_gained": record.actual_money_gained or 0,
                        "execution_time": record.execution_time or 0
                    }
                    for record in recent_records
                ]
            }
        }

    except Exception as e:
        logger.error(f"获取签到任务信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取签到任务信息失败: {str(e)}")


@router.get("/test")
async def test_checkin_system(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """测试签到系统"""
    try:
        from services.crawler.http_client import HttpClient

        http_client = HttpClient(max_concurrent=1, timeout=30)
        await http_client.create()

        try:
            response = await http_client.get("https://sehuatang.org/forum.php")
            if response.status_code != 200:
                return {"success": False, "message": f"无法访问论坛，状态码: {response.status_code}"}

            if "登录" in response.text and "用户名" in response.text:
                return {"success": False, "message": "Cookie已失效，需要重新登录"}

        finally:
            await http_client.close()

        config = db.query(CheckInConfig).first()
        if not config:
            config = CheckInConfig()

        return {
            "success": True,
            "message": "签到系统测试通过，Cookie有效",
            "data": {
                "cookie_available": True,
                "config_enabled": config.enabled,
                "target_board": config.target_board,
                "reply_count": config.reply_count_per_day,
                "checkin_url": auto_checkin_service.checkin_url
            }
        }

    except Exception as e:
        logger.error(f"测试签到系统失败: {e}")
        return {"success": False, "message": f"测试失败: {str(e)}"}


# === 定时任务函数 ===

async def scheduled_checkin_task():
    """供调度器调用的签到任务"""
    try:
        logger.info("🕐 定时签到任务开始执行")
        result = await auto_checkin_service.perform_daily_checkin()
        logger.info(f"定时签到任务完成: {result}")
        return result
    except Exception as e:
        logger.error(f"定时签到任务异常: {e}")
        return {'success': False, 'message': str(e)}
