#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器
"""

import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def init_scheduler() -> AsyncIOScheduler:
    """初始化调度器"""
    global _scheduler
    
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        logger.info("调度器初始化完成")
    
    return _scheduler


def start_scheduler() -> None:
    """启动调度器"""
    global _scheduler
    
    if _scheduler is None:
        init_scheduler()
    
    if not _scheduler.running:
        _scheduler.start()
        logger.info("调度器已启动")


def stop_scheduler() -> None:
    """停止调度器"""
    global _scheduler
    
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("调度器已停止")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """获取调度器实例"""
    return _scheduler


def add_subscription_job(
    subscription_id: int,
    cron_expression: str,
    job_id: Optional[str] = None
) -> None:
    """
    添加订阅定时任务
    
    Args:
        subscription_id: 订阅ID
        cron_expression: Cron表达式
        job_id: 任务ID
    """
    if not _scheduler:
        init_scheduler()
    
    if not job_id:
        job_id = f"subscription_{subscription_id}"
    
    # 解析Cron表达式
    parts = cron_expression.split()
    if len(parts) >= 5:
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2] if parts[2] != '*' else None,
            month=parts[3] if parts[3] != '*' else None,
            day_of_week=parts[4] if parts[4] != '*' else None,
            timezone="Asia/Shanghai"
        )
        
        from services.crawler.engine import run_subscription
        
        _scheduler.add_job(
            func=run_subscription,
            args=[subscription_id, 'scheduled'],
            trigger=trigger,
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"添加定时任务: {job_id}, Cron: {cron_expression}")


def remove_subscription_job(subscription_id: int) -> None:
    """移除订阅定时任务"""
    if not _scheduler:
        return
    
    job_id = f"subscription_{subscription_id}"
    _scheduler.remove_job(job_id)
    logger.info(f"移除定时任务: {job_id}")


def add_checkin_job(
    hour: int = 10,
    minute: int = 0,
    job_id: str = "daily_checkin"
) -> None:
    """添加每日签到任务"""
    if not _scheduler:
        init_scheduler()
    
    from services.checkin_service import run_daily_checkin
    
    _scheduler.add_job(
        func=run_daily_checkin,
        trigger=CronTrigger(hour=hour, minute=minute, timezone="Asia/Shanghai"),
        id=job_id,
        replace_existing=True
    )
    
    logger.info(f"添加每日签到任务: {hour:02d}:{minute:02d}")


def list_jobs() -> list:
    """列出所有任务"""
    if not _scheduler:
        return []
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })
    
    return jobs
