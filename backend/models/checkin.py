#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
签到模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index
from .base import Base


class CheckinConfig(Base):
    """签到配置"""
    __tablename__ = "checkin_config"
    
    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=True)
    
    # 定时配置
    schedule_hour = Column(Integer, default=10)
    schedule_minute = Column(Integer, default=0)
    random_delay_minutes = Column(Integer, default=30)  # 随机延迟
    
    # Telegram通知
    telegram_notifications_enabled = Column(Boolean, default=True)
    notify_before_checkin = Column(Boolean, default=True)
    notify_after_checkin = Column(Boolean, default=True)
    notify_on_failure = Column(Boolean, default=True)
    
    # Cookie关联
    cookie_id = Column(Integer, nullable=True)
    
    # 最后执行状态
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(50), nullable=True)
    last_run_message = Column(Text, nullable=True)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'enabled': self.enabled,
            'schedule_hour': self.schedule_hour,
            'schedule_minute': self.schedule_minute,
            'random_delay_minutes': self.random_delay_minutes,
            'telegram_notifications_enabled': self.telegram_notifications_enabled,
            'notify_before_checkin': self.notify_before_checkin,
            'notify_after_checkin': self.notify_after_checkin,
            'notify_on_failure': self.notify_on_failure,
            'cookie_id': self.cookie_id,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_run_status': self.last_run_status,
            'last_run_message': self.last_run_message,
        }


class CheckinRecord(Base):
    """签到记录"""
    __tablename__ = "checkin_records"
    
    id = Column(Integer, primary_key=True, index=True)
    checkin_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), nullable=False)  # success, failed, skipped
    
    # 奖励信息
    reward_type = Column(String(50), nullable=True)  # points, credits, bonus
    reward_amount = Column(Integer, nullable=True)
    reward_message = Column(Text, nullable=True)
    
    # 额外信息
    response_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Cookie信息
    cookie_id = Column(Integer, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_checkin_date', 'checkin_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'checkin_date': self.checkin_date.isoformat() if self.checkin_date else None,
            'status': self.status,
            'reward_type': self.reward_type,
            'reward_amount': self.reward_amount,
            'reward_message': self.reward_message,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
