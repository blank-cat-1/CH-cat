#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帖子模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index
from .base import Base


class Post(Base):
    """帖子模型"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    tid = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    
    # URL和内容
    original_url = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=True)
    
    # 作者信息
    author = Column(String(200), nullable=True, index=True)
    author_id = Column(String(50), nullable=True)
    
    # 板块信息
    board_name = Column(String(200), nullable=True, index=True)
    board_id = Column(String(20), nullable=True)
    type_name = Column(String(100), nullable=True)
    type_id = Column(String(20), nullable=True)
    
    # 下载链接
    magnet_link = Column(Text, nullable=True)
    ed2k_link = Column(Text, nullable=True)
    
    # 附件
    attachments = Column(JSON, nullable=True)  # [{name, url, size, type}]
    
    # 图片
    preview_image = Column(String(500), nullable=True)
    
    # 订阅关联
    subscription_id = Column(Integer, nullable=True, index=True)
    
    # 状态
    is_read = Column(Boolean, default=False, index=True)
    is_bookmarked = Column(Boolean, default=False)
    is_downloaded = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # 时间
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_posts_subscription_published', 'subscription_id', 'published_at'),
        Index('idx_posts_author_published', 'author', 'published_at'),
        Index('idx_posts_board_published', 'board_name', 'published_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'tid': self.tid,
            'title': self.title,
            'original_url': self.original_url,
            'content': self.content,
            'author': self.author,
            'author_id': self.author_id,
            'board_name': self.board_name,
            'board_id': self.board_id,
            'type_name': self.type_name,
            'type_id': self.type_id,
            'magnet_link': self.magnet_link,
            'ed2k_link': self.ed2k_link,
            'attachments': self.attachments,
            'preview_image': self.preview_image,
            'subscription_id': self.subscription_id,
            'is_read': self.is_read,
            'is_bookmarked': self.is_bookmarked,
            'is_downloaded': self.is_downloaded,
            'is_deleted': self.is_deleted,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
