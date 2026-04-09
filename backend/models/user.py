#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from .base import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 用户角色
    role = Column(String(50), default="user")  # admin, user, guest
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Telegram绑定
    telegram_id = Column(String(100), nullable=True, index=True)
    telegram_chat_id = Column(String(100), nullable=True)
    
    # 通知设置
    notify_on_new_posts = Column(Boolean, default=True)
    notify_on_errors = Column(Boolean, default=True)
    telegram_notifications_enabled = Column(Boolean, default=True)
    
    # 统计
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_users_role', 'role'),
        Index('idx_users_telegram', 'telegram_id'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'telegram_id': self.telegram_id,
            'notify_on_new_posts': self.notify_on_new_posts,
            'notify_on_errors': self.notify_on_errors,
            'telegram_notifications_enabled': self.telegram_notifications_enabled,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
