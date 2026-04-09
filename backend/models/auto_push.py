#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动推送模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index
from .base import Base


class AutoPushRule(Base):
    """自动推送规则"""
    __tablename__ = "auto_push_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 触发条件
    subscription_id = Column(Integer, nullable=True, index=True)
    keywords = Column(Text, nullable=True)  # 触发关键词，逗号分隔
    exclude_keywords = Column(Text, nullable=True)  # 排除关键词
    
    # 推送配置
    push_enabled = Column(Boolean, default=True)
    push_targets = Column(JSON, nullable=True)  # ["telegram", "emby", "webhook"]
    record_only = Column(Boolean, default=False)  # 仅记录，不推送
    
    # 定时配置
    cron_schedule = Column(String(100), nullable=True)
    
    # 统计
    total_triggers = Column(Integer, default=0)
    last_triggered_at = Column(DateTime, nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_auto_push_subscription', 'subscription_id'),
        Index('idx_auto_push_active', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'subscription_id': self.subscription_id,
            'keywords': self.keywords,
            'exclude_keywords': self.exclude_keywords,
            'push_enabled': self.push_enabled,
            'push_targets': self.push_targets,
            'record_only': self.record_only,
            'cron_schedule': self.cron_schedule,
            'total_triggers': self.total_triggers,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            'is_active': self.is_active,
        }


class AutoPushLog(Base):
    """自动推送日志"""
    __tablename__ = "auto_push_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False, index=True)
    post_id = Column(Integer, nullable=True)
    
    # 推送结果
    status = Column(String(50), nullable=False)  # success, failed, skipped
    target = Column(String(50), nullable=True)  # telegram, emby, webhook
    error_message = Column(Text, nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'post_id': self.post_id,
            'status': self.status,
            'target': self.target,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
