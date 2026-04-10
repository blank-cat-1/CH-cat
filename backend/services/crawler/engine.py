#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫引擎 - 订阅爬虫主入口
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
import logging

from .http_client import HttpClient
from .parser import parse_forum_threads, parse_search_threads, parse_user_threads, parse_detail
from .cookies import get_active_cookies
from .crawler_models import ThreadSummary, PostData
from ...models import Post, Subscription
from ...core.logging_config import CrawlerLogger

logger = logging.getLogger(__name__)


class SubscriptionCrawler:
    """订阅爬虫"""

    def __init__(self, subscription_id: int, use_selenium: bool = True):
        self.subscription_id = subscription_id
        self.subscription: Optional[Dict[str, Any]] = None
        self.http_client: Optional[HttpClient] = None
        self.logger = CrawlerLogger(subscription_id)
        self.state = {}  # 运行状态
        self.total_new_posts = 0
        self.total_duration = 0.0
        self.use_selenium = use_selenium
    
    async def run(self, trigger_type: str = 'manual') -> int:
        """
        运行订阅爬虫
        
        Args:
            trigger_type: 触发类型 (manual, scheduled, api)
            
        Returns:
            新增帖子数量
        """
        start_time = time.time()
        
        try:
            # 0. Selenium 模式下不再强制检查 Cookie
            if not self.use_selenium:
                cookies = get_active_cookies()
                if not cookies:
                    logger.error(f"订阅 {self.subscription_id} 无法运行: Cookie未配置!")
                    logger.error("请先通过 POST /api/crawler/cookies 配置Cookie 或使用 Selenium 模式")
                    return 0

            # 1. 加载订阅配置
            self.subscription = await self._load_subscription()
            if not self.subscription:
                logger.error(f"订阅 {self.subscription_id} 不存在")
                return 0
            
            # 检查订阅是否激活
            if not self.subscription.get('is_active', True):
                logger.warning(f"订阅 {self.subscription_id} 未激活，跳过执行")
                return 0
            
            # 2. 初始化HTTP客户端 (Selenium 模式)
            self.http_client = HttpClient(use_selenium=self.use_selenium)
            await self.http_client.create()
            
            # 3. 确定运行模式
            phase = self.subscription.get('phase', 'watch')
            is_backfill = phase == 'backfill'
            mode = "backfill" if is_backfill else "watch"
            
            # 4. 构造来源列表
            sources = self._build_sources()
            
            # 5. 记录启动信息
            page_range = f"{self.subscription.get('page_start', 1)}-{self.subscription.get('page_end', 'end')}"
            self.logger.start_subscription(
                self.subscription.get('name', '未命名'),
                mode,
                page_range
            )
            
            # 6. 爬取各个来源
            for source_key, source_config in sources.items():
                count = await self._crawl_source(source_key, source_config, is_backfill)
                self.total_new_posts += count
            
            # 7. 标记首次运行完成（回填模式）
            if is_backfill and self.total_new_posts > 0:
                self._mark_first_run_complete()
            
            # 8. 发送通知
            if not is_backfill and self.total_new_posts > 0:
                await self._send_notification()
            
            self.total_duration = time.time() - start_time
            self.logger.subscription_complete(self.total_new_posts, self.total_duration)
            
            return self.total_new_posts
            
        except Exception as e:
            self.total_duration = time.time() - start_time
            self.logger.subscription_error(f"{str(e)} | 耗时{self.total_duration:.1f}s")
            logger.error(f"订阅 {self.subscription_id} 爬取失败: {e}", exc_info=True)
            return 0
        finally:
            if self.http_client:
                await self.http_client.close()
    
    async def _load_subscription(self) -> Optional[Dict[str, Any]]:
        """从数据库加载订阅配置"""
        try:
            from ...core.database import get_db_session
            
            with get_db_session() as db:
                sub = db.query(Subscription).filter(Subscription.id == self.subscription_id).first()
                if sub:
                    return {
                        'id': sub.id,
                        'name': sub.name,
                        'phase': sub.phase,
                        'is_active': sub.enabled,
                        'page_start': sub.page_start or 1,
                        'page_end': sub.page_end or 10,
                        'max_pages_per_run': sub.max_pages_per_run or 20,
                        'include_keywords': sub.include_keywords or '',
                        'exclude_keywords': sub.exclude_keywords or '',
                        'secondary_keywords': sub.secondary_keywords or '',
                        'skip_locked': sub.skip_locked or False,
                        'fid': sub.fid,
                        'typeids': sub.typeids or [],
                    }
                return None
        except Exception as e:
            logger.error(f"加载订阅配置失败: {e}")
            return None
    
    def _build_sources(self) -> Dict[str, Dict[str, Any]]:
        """构造爬取来源列表"""
        sources = {}
        
        if not self.subscription:
            return sources
        
        base_url = "https://www.sehuatang.org"
        fid = self.subscription.get('fid')
        typeids = self.subscription.get('typeids', [])
        
        if fid:
            if typeids:
                for typeid in typeids:
                    source_key = f"forum_{fid}_typeid_{typeid}"
                    sources[source_key] = {
                        'type': 'forum_filtered',
                        'url': f"{base_url}/forum.php?mod=forumdisplay&fid={fid}&filter=typeid&typeid={typeid}&page={{page}}",
                        'parser': 'forum'
                    }
            else:
                source_key = f"forum_{fid}"
                sources[source_key] = {
                    'type': 'forum',
                    'url': f"{base_url}/forum.php?mod=forumdisplay&fid={fid}&page={{page}}",
                    'parser': 'forum'
                }
        
        return sources
    
    async def _crawl_source(self, source_key: str, source_config: Dict[str, Any], is_backfill: bool) -> int:
        """爬取单个来源"""
        logger.info(f"开始爬取来源: {source_key}")
        
        try:
            total_new_posts = 0
            max_pages = self.subscription.get('max_pages_per_run', 20) if not is_backfill else float('inf')
            page_start = self.subscription.get('page_start', 1) if is_backfill else 1
            page_end = self.subscription.get('page_end', 10) if is_backfill else 10
            
            for page_num in range(max_pages):
                actual_page = page_start + page_num
                
                if actual_page > page_end:
                    break
                
                # 构造URL
                url = source_config['url'].format(page=actual_page)
                
                # 获取帖子列表
                threads = await self._fetch_list_page(url, source_config['parser'])
                
                if not threads:
                    logger.warning(f"第 {actual_page} 页为空")
                    continue
                
                # 过滤帖子
                filtered_threads = self._filter_threads(threads)
                
                if not filtered_threads:
                    continue
                
                # 获取详情
                posts = await self._fetch_details(filtered_threads)
                
                # 保存到数据库
                saved = await self._save_posts(posts)
                total_new_posts += saved
                
                self.logger.page_result(actual_page, len(threads), len(filtered_threads))
            
            return total_new_posts
            
        except Exception as e:
            logger.error(f"爬取来源 {source_key} 失败: {e}")
            return 0
    
    async def _fetch_list_page(self, url: str, parser_type: str) -> List[ThreadSummary]:
        """获取列表页"""
        try:
            response = await self.http_client.get(url)
            if response.status_code != 200:
                return []
            
            if parser_type == 'forum':
                return parse_forum_threads(response.text, url)
            elif parser_type == 'search':
                return parse_search_threads(response.text, url)
            elif parser_type == 'user':
                return parse_user_threads(response.text, url)
            else:
                return parse_forum_threads(response.text, url)
                
        except Exception as e:
            logger.error(f"获取列表页失败: {url}, {e}")
            return []
    
    async def _fetch_details(self, threads: List[ThreadSummary]) -> List[PostData]:
        """获取详情页"""
        posts = []
        semaphore = asyncio.Semaphore(4)  # 限制并发
        
        async def fetch_one(thread: ThreadSummary) -> Optional[PostData]:
            async with semaphore:
                try:
                    response = await self.http_client.get(thread.url)
                    if response.status_code != 200:
                        return None
                    
                    post_data = parse_detail(response.text, thread.url)
                    post_data.tid = thread.tid
                    post_data.title = thread.title
                    post_data.author = thread.author
                    post_data.author_id = thread.author_id
                    post_data.published_at = thread.published_at
                    return post_data
                    
                except Exception as e:
                    logger.warning(f"获取详情失败: {thread.url}, {e}")
                    return None
        
        tasks = [fetch_one(t) for t in threads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, PostData):
                posts.append(result)
        
        return posts
    
    def _filter_threads(self, threads: List[ThreadSummary]) -> List[ThreadSummary]:
        """过滤帖子"""
        if not threads:
            return []
        
        include_keywords = self.subscription.get('include_keywords', '')
        exclude_keywords = self.subscription.get('exclude_keywords', '')
        
        include_list = [kw.strip().lower() for kw in include_keywords.split(',') if kw.strip()]
        exclude_list = [kw.strip().lower() for kw in exclude_keywords.split(',') if kw.strip()]
        
        filtered = []
        for thread in threads:
            title = thread.title.lower() if thread.title else ''
            
            # 必须包含关键词
            if include_list and not any(kw in title for kw in include_list):
                continue
            
            # 不能包含排除关键词
            if exclude_list and any(kw in title for kw in exclude_list):
                continue
            
            filtered.append(thread)
        
        return filtered
    
    async def _save_posts(self, posts: List[PostData]) -> int:
        """保存帖子到数据库"""
        if not posts:
            return 0
        
        try:
            from ...core.database import get_db_session
            
            with get_db_session() as db:
                saved_count = 0
                
                for post_data in posts:
                    # 检查是否已存在
                    existing = db.query(Post).filter(Post.tid == post_data.tid).first()
                    if existing:
                        continue
                    
                    # 创建帖子记录
                    post = Post(
                        title=post_data.title,
                        tid=post_data.tid,
                        original_url=post_data.url,
                        author=post_data.author,
                        author_id=post_data.author_id,
                        magnet_link=post_data.magnet_link,
                        attachments=post_data.attachments,
                        preview_image=post_data.preview_image,
                        subscription_id=self.subscription_id,
                        board_name=post_data.board_name,
                        type_name=post_data.type_name,
                        published_at=post_data.published_at
                    )
                    db.add(post)
                    saved_count += 1
                
                # 注意: get_db_session 会自动 commit
                return saved_count
                
        except Exception as e:
            logger.error(f"保存帖子失败: {e}")
            return 0
    
    def _mark_first_run_complete(self):
        """标记首次运行完成"""
        try:
            from ...core.database import get_db_session
            
            with get_db_session() as db:
                sub = db.query(Subscription).filter(Subscription.id == self.subscription_id).first()
                if sub:
                    sub.first_run_completed = True
                    # get_db_session 会自动 commit
                    logger.info(f"订阅 {self.subscription_id} 首次运行完成")
        except Exception as e:
            logger.warning(f"标记首次运行完成失败: {e}")
    
    async def _send_notification(self):
        """发送完成通知"""
        try:
            from ..notification import NotificationService
            notification = NotificationService()
            await notification.send_subscription_complete(
                subscription=self.subscription,
                new_posts=self.total_new_posts,
                duration=self.total_duration
            )
        except Exception as e:
            logger.warning(f"发送通知失败: {e}")


async def run_subscription(sub_id: int, trigger_type: str = 'manual', use_selenium: bool = True) -> int:
    """
    运行订阅爬虫的便捷函数

    Args:
        sub_id: 订阅ID
        trigger_type: 触发类型
        use_selenium: 是否使用 Selenium 模式（自动维护Cookie）

    Returns:
        新增帖子数量
    """
    crawler = SubscriptionCrawler(sub_id, use_selenium=use_selenium)
    return await crawler.run(trigger_type)
