#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core import get_db, settings
from models import User

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    # 简单的管理员验证
    if request.username == "admin":
        if request.password == settings.admin_password:
            return LoginResponse(
                success=True,
                token="admin-token-" + settings.admin_password,
                user={"username": "admin", "role": "admin"},
                message="登录成功"
            )
        else:
            raise HTTPException(status_code=401, detail="密码错误")
    
    # 数据库用户验证
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="用户已禁用")
    
    # 简单密码验证（生产环境应使用哈希）
    if user.password_hash != request.password:
        raise HTTPException(status_code=401, detail="密码错误")
    
    # 更新登录统计
    user.login_count += 1
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    return LoginResponse(
        success=True,
        token=f"user-token-{user.id}",
        user={"username": user.username, "role": user.role},
        message="登录成功"
    )


@router.post("/logout")
async def logout():
    """用户登出"""
    return {"success": True, "message": "已登出"}


@router.get("/me")
async def get_current_user():
    """获取当前用户信息"""
    # 简化版：默认返回管理员
    return {
        "username": "admin",
        "role": "admin"
    }
