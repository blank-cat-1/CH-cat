#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
签到相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date
from sqlalchemy.sql import func
from .base import Base


class CheckInRecord(Base):
    """签到记录表"""
    __tablename__ = "checkin_records"
    
    id = Column(Integer, primary_key=True, index=True)
    checkin_date = Column(Date, unique=True, index=True)  # 签到日期（每天只能签到一次）
    status = Column(String(20), default='success')  # success/failed/already_signed
    reply_count = Column(Integer, default=0)  # 当天回复数量
    
    # 签到前用户状态
    points_before = Column(Integer, default=0)  # 签到前积分
    money_before = Column(Integer, default=0)   # 签到前金钱
    coins_before = Column(Integer, default=0)   # 签到前色币
    
    # 签到后用户状态
    points_after = Column(Integer, default=0)   # 签到后积分
    money_after = Column(Integer, default=0)    # 签到后金钱
    coins_after = Column(Integer, default=0)    # 签到后色币
    
    # 实际收益（计算得出）
    actual_points_gained = Column(Integer, default=0)  # 实际获得积分
    actual_money_gained = Column(Integer, default=0)   # 实际获得金钱
    actual_coins_gained = Column(Integer, default=0)   # 实际获得色币
    
    # 保留原有字段（向后兼容）
    reward_points = Column(Integer, default=0)  # 签到返回的积分（可能不准确）
    reward_description = Column(String(500))  # 奖励描述
    error_message = Column(Text)  # 错误信息
    execution_time = Column(Integer)  # 执行时长（秒）
    replied_posts = Column(Text)  # 回复的帖子ID列表（JSON格式）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CheckInConfig(Base):
    """签到配置表"""
    __tablename__ = "checkin_config"
    
    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=True)  # 是否启用自动签到
    target_board = Column(String(100), default='情色分享')  # 目标板块
    reply_count_per_day = Column(Integer, default=3)  # 每日回复数量
    checkin_time = Column(String(20), default="09:00")  # 签到时间
    random_delay_min = Column(Integer, default=30)  # 随机延迟最小值（分钟）
    random_delay_max = Column(Integer, default=180)  # 随机延迟最大值（分钟）
    retry_count = Column(Integer, default=3)  # 重试次数
    notification_enabled = Column(Boolean, default=True)  # 是否启用通知
    telegram_notifications_enabled = Column(Boolean, default=True)  # 是否启用Telegram通知
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ReplyTemplate(Base):
    """回复模板表"""
    __tablename__ = "reply_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True)  # 模板分类
    content = Column(Text, nullable=False)  # 回复内容
    weight = Column(Integer, default=1)  # 权重（用于随机选择）
    enabled = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f'<ReplyTemplate {self.category}: {self.content[:20]}...>'
