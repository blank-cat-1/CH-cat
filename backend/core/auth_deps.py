#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证依赖 - 简化版
"""

from typing import Optional

from fastapi import Header, HTTPException

from models.user import User


async def get_current_user(x_session_token: Optional[str] = Header(None)) -> User:
    """
    获取当前用户 - 简化版
    实际项目中应该验证 session token 并从数据库获取用户
    """
    # 简化实现：直接返回管理员用户对象
    return User(id=1, username="admin", role="admin")
