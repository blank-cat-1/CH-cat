#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index
from .base import Base


class Subscription(Base):
    """订阅模型"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 订阅类型
    subscription_type = Column(String(50), default="forum")  # forum, keyword_search, author, custom
    
    # 论坛配置
    fid = Column(String(20), nullable=True)  # 论坛ID
    typeids = Column(JSON, nullable=True)  # 类型ID列表
    
    # 关键词配置
    keywords = Column(Text, nullable=True)  # 搜索关键词
    include_keywords = Column(Text, nullable=True)  # 包含关键词
    exclude_keywords = Column(Text, nullable=True)  # 排除关键词
    secondary_keywords = Column(Text, nullable=True)  # 次要关键词
    
    # 页面范围配置
    page_start = Column(Integer, default=1)
    page_end = Column(Integer, default=10)
    max_pages_per_run = Column(Integer, default=20)
    
    # 过滤配置
    skip_locked = Column(Boolean, default=False)  # 跳过锁定帖子
    require_magnet = Column(Boolean, default=False)  # 必须有磁力链接
    require_ed2k = Column(Boolean, default=False)  # 必须有ED2K链接
    min_magnet_count = Column(Integer, default=0)  # 最少磁力数量
    
    # 运行模式
    phase = Column(String(20), default="watch")  # watch, backfill, hybrid
    first_run_completed = Column(Boolean, default=False)
    auto_delete_when_complete = Column(Boolean, default=False)
    auto_switch_to_watch = Column(Boolean, default=False)
    
    # 定时配置
    cron_schedule = Column(String(100), nullable=True)  # Cron表达式
    enable_scheduled_task = Column(Boolean, default=True)
    timezone = Column(String(50), default="Asia/Shanghai")
    
    # 状态
    enabled = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # 统计
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(50), nullable=True)
    last_run_result = Column(Text, nullable=True)
    total_runs = Column(Integer, default=0)
    total_posts = Column(Integer, default=0)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_subscriptions_enabled', 'enabled'),
        Index('idx_subscriptions_fid', 'fid'),
        Index('idx_subscriptions_cron', 'cron_schedule'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'subscription_type': self.subscription_type,
            'fid': self.fid,
            'typeids': self.typeids,
            'keywords': self.keywords,
            'include_keywords': self.include_keywords,
            'exclude_keywords': self.exclude_keywords,
            'secondary_keywords': self.secondary_keywords,
            'page_start': self.page_start,
            'page_end': self.page_end,
            'max_pages_per_run': self.max_pages_per_run,
            'skip_locked': self.skip_locked,
            'require_magnet': self.require_magnet,
            'require_ed2k': self.require_ed2k,
            'min_magnet_count': self.min_magnet_count,
            'phase': self.phase,
            'first_run_completed': self.first_run_completed,
            'auto_delete_when_complete': self.auto_delete_when_complete,
            'auto_switch_to_watch': self.auto_switch_to_watch,
            'cron_schedule': self.cron_schedule,
            'enable_scheduled_task': self.enable_scheduled_task,
            'timezone': self.timezone,
            'enabled': self.enabled,
            'is_active': self.is_active,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_run_status': self.last_run_status,
            'last_run_result': self.last_run_result,
            'total_runs': self.total_runs,
            'total_posts': self.total_posts,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
