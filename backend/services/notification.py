#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务 - 统一的通知发送
"""

import logging
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.telegram_enabled = False
        self._init_telegram()
    
    def _init_telegram(self):
        """初始化Telegram"""
        try:
            from ..core.config import settings
            if settings.telegram_bot_token:
                self.telegram_enabled = True
                logger.info("Telegram通知已启用")
        except Exception as e:
            logger.warning(f"Telegram初始化失败: {e}")
    
    async def send_subscription_complete(
        self,
        subscription: Dict[str, Any],
        new_posts: int,
        duration: float
    ):
        """发送订阅完成通知"""
        if not self.telegram_enabled:
            return
        
        try:
            message = self._format_subscription_message(subscription, new_posts, duration)
            await self._send_telegram(message)
        except Exception as e:
            logger.error(f"发送订阅通知失败: {e}")
    
    async def send_subscription_error(
        self,
        subscription: Dict[str, Any],
        error: str
    ):
        """发送订阅错误通知"""
        if not self.telegram_enabled:
            return
        
        try:
            message = f"❌ 订阅错误\n\n订阅: {subscription.get('name', '未知')}\n错误: {error}"
            await self._send_telegram(message)
        except Exception as e:
            logger.error(f"发送错误通知失败: {e}")
    
    async def _send_telegram(self, message: str):
        """发送Telegram消息"""
        try:
            import httpx
            from ..core.config import settings
            
            url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": settings.telegram_webhook_url or "",
                "text": message,
                "parse_mode": "HTML"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.debug("Telegram消息发送成功")
            else:
                logger.warning(f"Telegram消息发送失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Telegram发送异常: {e}")
    
    def _format_subscription_message(
        self,
        subscription: Dict[str, Any],
        new_posts: int,
        duration: float
    ) -> str:
        """格式化订阅消息"""
        name = subscription.get('name', '未知订阅')
        phase = subscription.get('phase', 'watch')
        
        return f"""📬 订阅爬取完成

订阅: {name}
模式: {phase}
新增帖子: {new_posts}
耗时: {duration:.1f}秒"""


class CookieAutoChecker:
    """Cookie自动检查器"""
    
    def __init__(self, interval_minutes: int = 10):
        self.interval_minutes = interval_minutes
        self._running = False
        self._task = None
    
    def start(self):
        """启动检查器"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info(f"Cookie自动检查器已启动 (间隔{self.interval_minutes}分钟)")
    
    def stop(self):
        """停止检查器"""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Cookie自动检查器已停止")
    
    async def _check_loop(self):
        """检查循环"""
        while self._running:
            try:
                await self._check_cookies()
            except Exception as e:
                logger.error(f"Cookie检查异常: {e}")
            
            await asyncio.sleep(self.interval_minutes * 60)
    
    async def _check_cookies(self):
        """检查Cookie是否有效"""
        try:
            from .crawler.cookies import get_active_cookies, validate_cookies
            
            cookies = get_active_cookies()
            if cookies and not validate_cookies(cookies):
                logger.warning("Cookie可能已过期")
        except Exception as e:
            logger.error(f"Cookie验证失败: {e}")
