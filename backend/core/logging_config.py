#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志配置
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from .config import settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    设置统一的日志配置
    
    Args:
        log_level: 日志级别，默认使用配置文件中的设置
    """
    # 确定日志级别
    level = log_level or settings.log_level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器 - 按日期轮转
    log_file = log_dir / "app.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 关闭第三方库的详细日志
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info(f"日志系统初始化完成，日志级别: {level}")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        配置好的日志器
    """
    return logging.getLogger(name)


class CrawlerLogger:
    """爬虫专用日志记录器"""
    
    def __init__(self, subscription_id: int):
        self.logger = logging.getLogger(f"crawler.{subscription_id}")
        self.subscription_id = subscription_id
    
    def start_subscription(self, name: str, mode: str, page_range: str):
        self.logger.info(f"🚀 开始订阅: {name}, 模式: {mode}, 页码: {page_range}")
    
    def start_page(self, page: int, url: str):
        self.logger.info(f"📄 开始爬取第 {page} 页: {url}")
    
    def page_empty(self, page: int):
        self.logger.warning(f"⚠️ 第 {page} 页为空")
    
    def page_empty(self, page: int):
        self.logger.warning(f"⚠️ 第 {page} 页为空")
    
    def page_result(self, page: int, total: int, filtered: int):
        self.logger.info(f"📊 第 {page} 页: 发现 {total} 个帖子，过滤后 {filtered} 个")
    
    def thread_result(self, title: str, status: str, detail: Optional[str] = None, url: str = "", page: int = 0):
        detail_str = f" ({detail})" if detail else ""
        self.logger.info(f"{'✅' if '成功' in status or '已保存' in status else '❌'} {title[:30]}... {status}{detail_str}")
    
    def download_links(self, title: str, magnets: int, ed2k: int, attachments: int, url: str = "", page: int = 0):
        links = []
        if magnets > 0:
            links.append(f"{magnets}个磁力")
        if ed2k > 0:
            links.append(f"{ed2k}个ED2K")
        if attachments > 0:
            links.append(f"{attachments}个附件")
        links_str = ", ".join(links)
        self.logger.info(f"📎 {title[:30]}...: {links_str}")
    
    def subscription_complete(self, new_posts: int, duration: float):
        self.logger.info(f"✅ 订阅爬取完成: 新增 {new_posts} 个帖子, 耗时 {duration:.2f}s")
    
    def subscription_error(self, error: str):
        self.logger.error(f"❌ 订阅爬取出错: {error}")
    
    def consecutive_empty(self, count: int):
        self.logger.warning(f"⚠️ 连续 {count} 页为空，停止爬取")
