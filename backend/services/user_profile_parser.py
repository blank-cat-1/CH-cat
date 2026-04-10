#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户资料解析器
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UserProfileStats:
    username: str = ""
    uid: str = ""
    points: int = 0
    money: int = 0
    coins: int = 0
    level: str = "未知"


class UserProfileParser:
    """用户资料解析器"""

    async def get_user_profile_stats(self, cookie_str: str = None) -> Optional[UserProfileStats]:
        """获取用户资料"""
        try:
            from services.crawler.http_client import HttpClient

            http_client = HttpClient(max_concurrent=1, timeout=30)
            await http_client.create()

            try:
                response = await http_client.get("https://sehuatang.org/forum.php")

                if response.status_code != 200:
                    logger.warning(f"获取用户资料失败: HTTP {response.status_code}")
                    return None

                html = response.text

                # 解析用户资料
                return self.parse_from_profile(html)

            finally:
                await http_client.close()

        except Exception as e:
            logger.error(f"获取用户资料异常: {e}")
            return None

    def parse_from_profile(self, html: str) -> Optional[UserProfileStats]:
        """从HTML解析用户资料"""
        try:
            stats = UserProfileStats()

            # 解析用户名
            username_match = re.search(r'<a href="home\.php\?mod=space&amp;uid=\d+"[^>]*>([^<]+)</a>', html)
            if username_match:
                stats.username = username_match.group(1).strip()

            # 解析UID
            uid_match = re.search(r'home\.php\?mod=space&amp;uid=(\d+)', html)
            if uid_match:
                stats.uid = uid_match.group(1)

            # 解析积分 (魔法表情后面的数字)
            points_patterns = [
                r'扩展阅读.*?<span[^>]*>\s*(\d+)\s*</span>',
                r'积分.*?<span[^>]*>\s*(\d+)\s*</span>',
                r'class="xi1".*?(\d+).*?积分',
            ]
            for pattern in points_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    stats.points = int(match.group(1))
                    break

            # 解析金钱
            money_patterns = [
                r'金钱.*?<span[^>]*>\s*(\d+)\s*</span>',
                r'金钱.*?<[^>]+>\s*(\d+)',
            ]
            for pattern in money_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    stats.money = int(match.group(1))
                    break

            # 解析色币
            coins_patterns = [
                r'色币.*?<span[^>]*>\s*(\d+)\s*</span>',
                r'色币.*?<[^>]+>\s*(\d+)',
            ]
            for pattern in coins_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    stats.coins = int(match.group(1))
                    break

            return stats

        except Exception as e:
            logger.error(f"解析用户资料异常: {e}")
            return None


# 全局实例
user_profile_parser = UserProfileParser()
