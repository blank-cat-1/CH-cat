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


@router.get("/status")
async def get_crawler_status():
    """获取爬虫状态"""
    cookies = get_active_cookies()
    
    return {
        "status": "running",
        "cookies_loaded": cookies is not None,
        "cookies_valid": validate_cookies(cookies) if cookies else False,
        "rate_limit": "8 req/s",
        "max_concurrent": 12
    }


@router.get("/cookies")
async def get_cookies():
    """获取当前Cookie"""
    cookies = get_active_cookies()
    
    if not cookies:
        return {
            "has_cookies": False,
            "message": "未配置Cookie"
        }
    
    # 隐藏敏感信息
    cookie_list = []
    for item in cookies.split(';'):
        if '=' in item:
            key = item.split('=')[0].strip()
            cookie_list.append({"key": key, "value": "***"})
    
    return {
        "has_cookies": True,
        "count": len(cookie_list),
        "cookies": cookie_list
    }


@router.post("/cookies")
async def update_cookies(data: CookieUpdate):
    """更新Cookie"""
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
