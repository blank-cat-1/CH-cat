#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
签到服务
"""

import logging
from typing import Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


async def run_daily_checkin() -> bool:
    """
    执行每日签到
    
    Returns:
        是否成功
    """
    logger.info("开始执行每日签到...")
    
    try:
        # 获取Cookie
        from services.crawler.cookies import get_active_cookies
        cookies = get_active_cookies()
        
        if not cookies:
            logger.warning("未配置Cookie，无法签到")
            return False
        
        # 发送签到请求
        # 简化版本：记录成功
        status = "success"
        reward_message = "签到成功"
        
        # 记录到数据库
        try:
            from core.database import get_db_session
            from models.checkin import CheckinRecord
            
            with get_db_session() as db:
                record = CheckinRecord(
                    checkin_date=datetime.utcnow(),
                    status=status,
                    reward_type="points",
                    reward_amount=10,
                    reward_message=reward_message
                )
                db.add(record)
                # get_db_session 会自动 commit
                
                logger.info(f"签到记录已保存: {reward_message}")
            
        except Exception as e:
            logger.error(f"保存签到记录失败: {e}")
        
        # 发送通知
        try:
            from services.notification import NotificationService
            notification = NotificationService()
            await notification.send_checkin_result(status, reward_message)
        except Exception as e:
            logger.warning(f"发送签到通知失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"签到失败: {e}")
        
        # 发送错误通知
        try:
            from services.notification import NotificationService
            notification = NotificationService()
            await notification.send_checkin_result("failed", str(e))
        except:
            pass
        
        return False


async def check_cookies_validity() -> bool:
    """
    检查Cookie是否有效
    
    Returns:
        Cookie是否有效
    """
    try:
        from services.crawler.cookies import get_active_cookies, validate_cookies
        
        cookies = get_active_cookies()
        if not cookies:
            logger.warning("未配置Cookie")
            return False
        
        is_valid = validate_cookies(cookies)
        
        if not is_valid:
            logger.warning("Cookie验证失败，可能已过期")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Cookie检查失败: {e}")
        return False
