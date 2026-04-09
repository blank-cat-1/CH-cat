#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫管理路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from core import get_db
from services.crawler.cookies import get_active_cookies, save_cookies, validate_cookies

router = APIRouter()


class CookieUpdate(BaseModel):
    cookie_string: str
    name: str = "default"


class BrowserStatus(BaseModel):
    """浏览器状态"""
    is_running: bool
    cf_check_count: int
    cookie_count: int


@router.get("/status")
async def get_crawler_status():
    """获取爬虫状态"""
    cookies = get_active_cookies()

    # 获取 Selenium 浏览器状态
    browser_info = await get_browser_status()

    return {
        "status": "running",
        "mode": "selenium" if browser_info.get("is_running") else "httpx",
        "cookies_loaded": cookies is not None,
        "cookies_valid": validate_cookies(cookies) if cookies else True,  # Selenium 模式下允许为空
        "selenium_browser": browser_info,
        "rate_limit": "8 req/s",
        "max_concurrent": 12
    }


@router.get("/browser/status")
async def get_browser_status():
    """获取 Selenium 浏览器状态"""
    try:
        from services.crawler.selenium_browser import get_browser

        browser = await get_browser()
        is_running = browser.is_running if browser else False
        cf_count = browser._cf_check_count if browser else 0

        cookie_count = 0
        if is_running:
            cookies = await browser.get_cookies()
            cookie_count = len(cookies) if cookies else 0

        return {
            "is_running": is_running,
            "cf_check_count": cf_count,
            "cookie_count": cookie_count,
            "message": "浏览器运行中" if is_running else "浏览器未启动"
        }
    except Exception as e:
        return {
            "is_running": False,
            "cf_check_count": 0,
            "cookie_count": 0,
            "message": f"获取状态失败: {str(e)}"
        }


@router.post("/browser/start")
async def start_browser():
    """启动 Selenium 浏览器"""
    try:
        from services.crawler.selenium_browser import get_browser

        browser = await get_browser()
        success = await browser.init_browser()

        if success:
            # 访问目标站点，触发验证流程
            await browser.goto("https://www.sehuatang.org")

            return {
                "success": True,
                "message": "浏览器启动成功，Cookie自动维护已启用"
            }
        else:
            return {
                "success": False,
                "message": "浏览器启动失败，请检查是否安装了 selenium 和 chrome/chromedriver"
            }
    except ImportError as e:
        return {
            "success": False,
            "message": f"缺少依赖: {str(e)}，请运行: pip install selenium"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"启动失败: {str(e)}"
        }


@router.post("/browser/stop")
async def stop_browser():
    """停止 Selenium 浏览器"""
    try:
        from services.crawler.selenium_browser import close_browser

        await close_browser()

        return {
            "success": True,
            "message": "浏览器已关闭"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"关闭失败: {str(e)}"
        }


@router.post("/browser/restart")
async def restart_browser():
    """重启 Selenium 浏览器"""
    try:
        from services.crawler.selenium_browser import close_browser, get_browser

        # 先关闭
        await close_browser()

        # 再启动
        browser = await get_browser()
        success = await browser.init_browser()

        if success:
            await browser.goto("https://www.sehuatang.org")

            return {
                "success": True,
                "message": "浏览器重启成功"
            }
        else:
            return {
                "success": False,
                "message": "浏览器启动失败"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"重启失败: {str(e)}"
        }


@router.get("/cookies")
async def get_cookies():
    """获取当前Cookie"""
    cookies = get_active_cookies()

    # 尝试获取浏览器 Cookie
    browser_cookies = await get_browser_cookies()

    if not cookies and not browser_cookies:
        return {
            "has_cookies": False,
            "mode": "selenium" if browser_cookies else "manual",
            "message": "未配置Cookie"
        }

    # 构建响应
    cookie_list = []
    mode = "selenium"

    # 浏览器 Cookie
    if browser_cookies:
        for c in browser_cookies:
            cookie_list.append({
                "source": "browser",
                "name": c.get('name', ''),
                "domain": c.get('domain', ''),
                "value": "***"
            })

    # 手动 Cookie
    if cookies:
        mode = "hybrid"
        for item in cookies.split(';'):
            if '=' in item:
                key = item.split('=')[0].strip()
                cookie_list.append({
                    "source": "manual",
                    "name": key,
                    "value": "***"
                })

    return {
        "has_cookies": True,
        "mode": mode,
        "count": len(cookie_list),
        "cookies": cookie_list
    }


async def get_browser_cookies():
    """获取浏览器 Cookie"""
    try:
        from services.crawler.selenium_browser import get_browser

        browser = await get_browser()
        if browser and browser.is_running:
            return await browser.get_cookies()
        return []
    except:
        return []


@router.post("/cookies")
async def update_cookies(data: CookieUpdate):
    """更新Cookie (手动模式)"""
    if not validate_cookies(data.cookie_string):
        return {
            "success": False,
            "message": "Cookie格式无效，缺少必要字段"
        }

    success = save_cookies(data.cookie_string, data.name)

    return {
        "success": success,
        "message": "Cookie保存成功" if success else "Cookie保存失败"
    }


@router.delete("/cookies")
async def delete_cookies():
    """删除Cookie"""
    from services.crawler.cookies import delete_cookies as do_delete

    success = do_delete()

    return {
        "success": success,
        "message": "Cookie已删除" if success else "删除失败"
    }


@router.post("/cookies/sync")
async def sync_cookies():
    """同步浏览器Cookie到存储"""
    try:
        from services.crawler.cookies import sync_browser_cookies

        success = await sync_browser_cookies()

        return {
            "success": success,
            "message": "Cookie同步成功" if success else "Cookie同步失败"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"同步失败: {str(e)}"
        }
