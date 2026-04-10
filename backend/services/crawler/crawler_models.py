#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫数据模型 - 打破 engine 与 parser 的循环依赖
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ThreadSummary:
    """帖子摘要"""
    tid: str
    title: str
    url: str
    author: str
    author_id: Optional[str] = None
    published_at: Optional[datetime] = None
    board_name: Optional[str] = None
    board_id: Optional[str] = None


@dataclass
class PostData:
    """完整帖子数据"""
    tid: str
    title: str
    url: str
    author: str
    author_id: Optional[str] = None
    published_at: Optional[datetime] = None
    board_name: Optional[str] = None
    board_id: Optional[str] = None
    preview_image: Optional[str] = None
    magnet_link: Optional[str] = None
    attachments: Optional[List[Dict]] = None
    is_locked: bool = False
    type_id: Optional[int] = None
    type_name: Optional[str] = None
    content: Optional[str] = None
