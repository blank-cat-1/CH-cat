#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统日志模型 - 签到系统专用
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base


class SystemLog(Base):
    """系统日志模型"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    source = Column(String(50), nullable=False, index=True)  # 产生日志的模块
    message = Column(Text, nullable=False)  # 日志内容
    operation = Column(String(50), nullable=True)  # 操作类型
    details = Column(Text, nullable=True)  # 详细信息（JSON）
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 相关用户ID
    subscription_id = Column(Integer, nullable=True, index=True)  # 相关订阅ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
