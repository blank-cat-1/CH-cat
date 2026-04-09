#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie管理模块 - 支持手动和Selenium自动两种模式
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# 默认Cookie存储路径
DEFAULT_COOKIE_DIR = Path("data/cookies")
DEFAULT_COOKIE_FILE = DEFAULT_COOKIE_DIR / "cookies.json"


def get_active_cookies() -> Optional[str]:
    """
    获取当前激活的Cookie字符串

    Returns:
        Cookie字符串，格式为 "key1=value1; key2=value2"

    Note:
        在 Selenium 模式下，Cookie 由浏览器自动维护，此函数主要用于兼容旧代码。
        建议使用 get_active_cookies_async() 获取最新的浏览器 Cookie。
    """
    try:
        # 首先尝试从数据库获取
        try:
            from ...core.database import get_db_session
            from sqlalchemy import text

            with get_db_session() as db:
                result = db.execute(text("""
                    SELECT cookie_string
                    FROM cookies
                    WHERE is_active = true
                    ORDER BY last_used_at DESC
                    LIMIT 1
                """)).fetchone()

                if result and result[0]:
                    logger.debug("从数据库获取到激活的Cookie")
                    return result[0]
        except Exception as e:
            logger.debug(f"从数据库获取Cookie失败: {e}")

        # 回退到文件存储
        if DEFAULT_COOKIE_FILE.exists():
            with open(DEFAULT_COOKIE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('cookie_string'):
                    logger.debug("从文件获取到Cookie")
                    return data['cookie_string']

        # 在 Selenium 模式下，返回 None 是正常的，浏览器会自动处理
        logger.debug("未找到手动Cookie（Selenium模式会自动维护）")
        return None

    except Exception as e:
        logger.error(f"获取Cookie失败: {e}")
        return None


async def get_active_cookies_async() -> Optional[str]:
    """
    异步获取当前激活的Cookie字符串

    Returns:
        Cookie字符串，格式为 "key1=value1; key2=value2"
    """
    try:
        from .selenium_browser import get_browser

        browser = await get_browser()
        if browser and browser.is_running:
            return await browser.get_cookie_string()

        return get_active_cookies()

    except Exception as e:
        logger.error(f"异步获取Cookie失败: {e}")
        return get_active_cookies()


def save_cookies(cookie_string: str, name: str = "default", is_active: bool = True) -> bool:
    """
    保存Cookie

    Args:
        cookie_string: Cookie字符串
        name: Cookie名称
        is_active: 是否设为激活状态

    Returns:
        是否保存成功
    """
    try:
        # 确保目录存在
        DEFAULT_COOKIE_DIR.mkdir(parents=True, exist_ok=True)

        # 保存到文件
        data = {
            'name': name,
            'cookie_string': cookie_string,
            'updated_at': str(Path().resolve())
        }

        with open(DEFAULT_COOKIE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 尝试保存到数据库
        try:
            from ...core.database import get_db_session
            from sqlalchemy import text

            with get_db_session() as db:
                if is_active:
                    # 先取消所有Cookie的激活状态
                    db.execute(text("UPDATE cookies SET is_active = false"))

                # 插入新Cookie
                db.execute(text("""
                    INSERT INTO cookies (name, cookie_string, is_active, created_at, last_used_at)
                    VALUES (:name, :cookie_string, :is_active, NOW(), NOW())
                """), {
                    'name': name,
                    'cookie_string': cookie_string,
                    'is_active': is_active
                })

                logger.info("Cookie已保存到数据库")
        except Exception as e:
            logger.debug(f"保存Cookie到数据库失败: {e}")

        logger.info(f"Cookie已保存: {name}")
        return True

    except Exception as e:
        logger.error(f"保存Cookie失败: {e}")
        return False


def validate_cookies(cookie_string: str) -> bool:
    """
    验证Cookie是否有效

    Args:
        cookie_string: Cookie字符串

    Returns:
        是否有效

    Note:
        在 Selenium 模式下，Cookie 由浏览器自动验证，此函数主要用于手动模式。
    """
    if not cookie_string:
        # Selenium 模式下，cookie_string 为空是正常的
        logger.debug("Cookie为空（Selenium模式会自动处理）")
        return True

    # 检查必要的Cookie字段
    required_keys = ['a4517_auth', 'a4517_saltkey']
    cookies = {}

    for item in cookie_string.split(';'):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()

    for key in required_keys:
        if key not in cookies:
            logger.warning(f"Cookie缺少必要字段: {key}")
            return False

    return True


def delete_cookies(name: str = None) -> bool:
    """
    删除Cookie

    Args:
        name: Cookie名称，为None时删除所有

    Returns:
        是否删除成功
    """
    try:
        # 删除文件
        if DEFAULT_COOKIE_FILE.exists():
            if name is None:
                DEFAULT_COOKIE_FILE.unlink()
            else:
                try:
                    with open(DEFAULT_COOKIE_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data.get('name') == name:
                        DEFAULT_COOKIE_FILE.unlink()
                except:
                    pass

        # 从数据库删除
        try:
            from ...core.database import get_db_session
            from sqlalchemy import text

            with get_db_session() as db:
                if name:
                    db.execute(text("DELETE FROM cookies WHERE name = :name"), {'name': name})
                else:
                    db.execute(text("DELETE FROM cookies"))
        except Exception as e:
            logger.debug(f"从数据库删除Cookie失败: {e}")

        return True

    except Exception as e:
        logger.error(f"删除Cookie失败: {e}")
        return False


async def sync_browser_cookies() -> bool:
    """
    同步浏览器Cookie到存储

    Returns:
        是否同步成功
    """
    try:
        from .selenium_browser import get_browser

        browser = await get_browser()
        if not browser or not browser.is_running:
            logger.warning("浏览器未运行，无法同步Cookie")
            return False

        cookies = await browser.get_cookies()
        if cookies:
            # 保存到文件
            DEFAULT_COOKIE_DIR.mkdir(parents=True, exist_ok=True)
            with open(browser.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            # 保存到数据库
            try:
                from ...core.database import get_db_session
                from sqlalchemy import text

                cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

                with get_db_session() as db:
                    db.execute(text("UPDATE cookies SET is_active = false"))
                    db.execute(text("""
                        INSERT INTO cookies (name, cookie_string, is_active, created_at, last_used_at)
                        VALUES ('browser_auto', :cookie_string, true, NOW(), NOW())
                    """), {'cookie_string': cookie_string})
            except Exception as e:
                logger.debug(f"同步Cookie到数据库失败: {e}")

            logger.info(f"已同步 {len(cookies)} 个浏览器Cookie")
            return True

        return False

    except Exception as e:
        logger.error(f"同步浏览器Cookie失败: {e}")
        return False
