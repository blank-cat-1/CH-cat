#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
磁力链接模型（兼容旧版）
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index
from .base import Base


class MagnetLink(Base):
    """磁力链接模型"""
    __tablename__ = "magnet_links"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True)
    content = Column(Text)
    url = Column(String(500), unique=True, index=True)
    
    # 链接和代码
    magnets = Column(Text)  # JSON格式存储
    code = Column(String(100), index=True)
    magnet_hash = Column(String(64), index=True)
    
    # 图片
    images = Column(Text)  # JSON格式
    cover_url = Column(String(500))
    
    # 元数据
    size = Column(String(50))
    duration = Column(String(20))
    resolution = Column(String(20))
    format = Column(String(20))
    language = Column(String(50))
    subtitles = Column(Boolean, default=False)
    
    # 分类
    is_uncensored = Column(Boolean, default=False)
    forum_id = Column(String(10), index=True)
    forum_type = Column(String(20), index=True)
    author = Column(String(200), index=True)
    
    # 标签
    tags = Column(JSON)
    categories = Column(JSON)
    
    # Emby集成
    in_emby = Column(Boolean, index=True)
    emby_item_id = Column(String(100), index=True)
    emby_checked_at = Column(DateTime, nullable=True)
    
    # 统计
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    rating = Column(String(10))
    
    # 时间
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_magnet_code_forum', 'code', 'forum_id'),
        Index('idx_magnet_created', 'created_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'magnets': self.magnets,
            'code': self.code,
            'magnet_hash': self.magnet_hash,
            'images': self.images,
            'cover_url': self.cover_url,
            'size': self.size,
            'duration': self.duration,
            'resolution': self.resolution,
            'format': self.format,
            'language': self.language,
            'subtitles': self.subtitles,
            'is_uncensored': self.is_uncensored,
            'forum_id': self.forum_id,
            'forum_type': self.forum_type,
            'author': self.author,
            'tags': self.tags,
            'categories': self.categories,
            'in_emby': self.in_emby,
            'emby_item_id': self.emby_item_id,
            'emby_checked_at': self.emby_checked_at.isoformat() if self.emby_checked_at else None,
            'download_count': self.download_count,
            'view_count': self.view_count,
            'rating': self.rating,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
