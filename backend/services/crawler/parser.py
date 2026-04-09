#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面解析器 - 从HTML中提取帖子信息
"""

import re
from typing import List, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from .engine import ThreadSummary, PostData

logger = logging.getLogger(__name__)


def parse_forum_threads(html: str, base_url: str = "") -> List[ThreadSummary]:
    """
    解析论坛帖子列表页
    
    Args:
        html: HTML内容
        base_url: 基础URL
        
    Returns:
        帖子摘要列表
    """
    threads = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找帖子列表容器
        thread_list = soup.select('.threadlist tbody tr') or soup.select('#threadlist li')
        
        for item in thread_list:
            try:
                # 提取帖子标题和链接
                title_elem = item.select_one('.s xiang a') or item.select_one('a.xiang') or item.select_one('a[href*="thread"]')
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')
                
                # 提取TID
                tid_match = re.search(r'thread-(\d+)', href) or re.search(r'tid=(\d+)', href)
                if not tid_match:
                    continue
                tid = tid_match.group(1)
                
                # 提取作者
                author_elem = item.select_one('.by a') or item.select_one('.author')
                author = author_elem.get_text(strip=True) if author_elem else "未知"
                
                # 提取发布时间
                time_elem = item.select_one('.by span') or item.select_one('.time')
                published_at = None
                if time_elem:
                    time_str = time_elem.get_text(strip=True)
                    published_at = _parse_time(time_str)
                
                # 构建完整URL
                url = href if href.startswith('http') else f"https://www.sehuatang.org/{href.lstrip('/')}"
                
                threads.append(ThreadSummary(
                    tid=tid,
                    title=title,
                    url=url,
                    author=author,
                    published_at=published_at
                ))
                
            except Exception as e:
                logger.debug(f"解析帖子元素失败: {e}")
                continue
        
        logger.debug(f"解析到 {len(threads)} 个帖子")
        return threads
        
    except Exception as e:
        logger.error(f"解析论坛列表页失败: {e}")
        return []


def parse_search_threads(html: str, base_url: str = "") -> List[ThreadSummary]:
    """
    解析搜索结果页
    
    Args:
        html: HTML内容
        base_url: 基础URL
        
    Returns:
        帖子摘要列表
    """
    threads = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找搜索结果列表
        result_items = soup.select('.searchresult li') or soup.select('.result-item')
        
        for item in result_items:
            try:
                title_elem = item.select_one('a[href*="thread"]')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')
                
                tid_match = re.search(r'thread-(\d+)', href) or re.search(r'tid=(\d+)', href)
                if not tid_match:
                    continue
                tid = tid_match.group(1)
                
                author = "未知"
                author_elem = item.select_one('.author') or item.select_one('.by')
                if author_elem:
                    author = author_elem.get_text(strip=True)
                
                url = href if href.startswith('http') else f"https://www.sehuatang.org/{href.lstrip('/')}"
                
                threads.append(ThreadSummary(
                    tid=tid,
                    title=title,
                    url=url,
                    author=author
                ))
                
            except Exception:
                continue
        
        return threads
        
    except Exception as e:
        logger.error(f"解析搜索结果页失败: {e}")
        return []


def parse_user_threads(html: str, base_url: str = "") -> List[ThreadSummary]:
    """
    解析用户帖子列表页
    
    Args:
        html: HTML内容
        base_url: 基础URL
        
    Returns:
        帖子摘要列表
    """
    return parse_forum_threads(html, base_url)


def parse_detail(html: str, url: str) -> PostData:
    """
    解析帖子详情页
    
    Args:
        html: HTML内容
        url: 帖子URL
        
    Returns:
        帖子数据
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取标题
        title_elem = soup.select_one('.tsz b') or soup.select_one('h1') or soup.select_one('.thread-title')
        title = title_elem.get_text(strip=True) if title_elem else "无标题"
        
        # 提取正文内容
        content_elem = soup.select_one('.tpc_content') or soup.select_one('.post-content')
        content = content_elem.get_text(strip=True) if content_elem else ""
        
        # 提取磁力链接
        magnet_links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if 'magnet:' in href:
                magnet_links.append(href)
            elif href.startswith('ed2k:'):
                magnet_links.append(href)
        
        magnet_link = '\n'.join(magnet_links) if magnet_links else None
        
        # 提取图片
        images = []
        img_elem = soup.select('.tpc_content img') or soup.select('.post-content img')
        for img in img_elem:
            src = img.get('src') or img.get('data-src')
            if src and not src.endswith('.gif'):
                images.append(src)
        
        preview_image = images[0] if images else None
        
        # 提取附件
        attachments = []
        for att in soup.select('.t_attachments a') or soup.select('.attachment a'):
            att_href = att.get('href', '')
            att_name = att.get_text(strip=True)
            if att_href and att_name:
                attachments.append({
                    'name': att_name,
                    'url': att_href
                })
        
        # 判断是否锁定/需要回复可见
        is_locked = bool(soup.select('.locked') or soup.select('.reply-to-view'))
        
        # 提取作者
        author_elem = soup.select_one('.pi .by') or soup.select_one('.post-author')
        author = author_elem.get_text(strip=True) if author_elem else "未知"
        
        # 提取发布时间
        time_elem = soup.select_one('.authi span') or soup.select_one('.post-time')
        published_at = None
        if time_elem:
            time_str = time_elem.get_text(strip=True)
            published_at = _parse_time(time_str)
        
        # 提取TID
        tid_match = re.search(r'thread[/-](\d+)', url) or re.search(r'tid=(\d+)', url)
        tid = tid_match.group(1) if tid_match else ""
        
        return PostData(
            tid=tid,
            title=title,
            url=url,
            author=author,
            published_at=published_at,
            content=content,
            magnet_link=magnet_link,
            attachments=attachments if attachments else None,
            preview_image=preview_image,
            is_locked=is_locked
        )
        
    except Exception as e:
        logger.error(f"解析详情页失败: {url}, {e}")
        return PostData(
            tid="",
            title="解析失败",
            url=url,
            author="未知"
        )


def _parse_time(time_str: str) -> Optional[datetime]:
    """
    解析时间字符串
    
    Args:
        time_str: 时间字符串
        
    Returns:
        datetime对象
    """
    try:
        # 尝试多种格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%m-%d %H:%M",
            "%Y年%m月%d日 %H:%M",
            "%m月%d日 %H:%M"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
        
    except Exception:
        return None
