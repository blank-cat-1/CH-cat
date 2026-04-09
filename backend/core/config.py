#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # ==================== 应用基础配置 ====================
    app_name: str = Field(default="Sehuatang 爬虫系统", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # ==================== 日志配置 ====================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # ==================== 时区配置 ====================
    timezone: str = Field(default="Asia/Shanghai", env="TZ")
    
    # ==================== 服务器配置 ====================
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    api_base_url: str = Field(default="http://localhost:8000", env="API_BASE_URL")
    
    # ==================== 数据库配置 ====================
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_name: str = Field(default="sehuatang_dev", env="DATABASE_NAME")
    database_user: str = Field(default="postgres", env="DATABASE_USER")
    database_password: str = Field(default="", env="DATABASE_PASSWORD")
    
    # 数据库连接池配置
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # ==================== Redis配置 ====================
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # ==================== Telegram机器人配置 ====================
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_URL")
    telegram_use_webhook: bool = Field(default=False, env="TELEGRAM_USE_WEBHOOK")
    
    # ==================== 代理配置 ====================
    http_proxy: Optional[str] = Field(default=None, env="HTTP_PROXY")
    https_proxy: Optional[str] = Field(default=None, env="HTTPS_PROXY")
    
    # ==================== 安全配置 ====================
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    admin_password: str = Field(default="admin123", env="ADMIN_PASSWORD")
    
    # ==================== 文件存储配置 ====================
    upload_dir: str = Field(default="data/uploads", env="UPLOAD_DIR")
    log_dir: str = Field(default="logs", env="LOG_DIR")
    data_dir: str = Field(default="data", env="DATA_DIR")
    cookie_dir: str = Field(default="data/cookies", env="COOKIE_DIR")
    
    # ==================== 爬虫配置 ====================
    crawler_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", 
        env="CRAWLER_USER_AGENT"
    )
    crawler_timeout: int = Field(default=30, env="CRAWLER_TIMEOUT")
    crawler_retry_times: int = Field(default=3, env="CRAWLER_RETRY_TIMES")
    crawler_retry_delay: float = Field(default=1.0, env="CRAWLER_RETRY_DELAY")
    crawler_max_concurrent: int = Field(default=12, env="CRAWLER_MAX_CONCURRENT")
    crawler_rate_limit: float = Field(default=8.0, env="CRAWLER_RATE_LIMIT")
    
    # ==================== Emby集成配置 ====================
    emby_base_url: Optional[str] = Field(default=None, env="EMBY_BASE_URL")
    emby_api_key: Optional[str] = Field(default=None, env="EMBY_API_KEY")
    emby_user_id: Optional[str] = Field(default=None, env="EMBY_USER_ID")
    emby_library_ids: Optional[str] = Field(default=None, env="EMBY_LIBRARY_IDS")
    
    # ==================== FlareSolverr配置（可选，仅非Selenium模式备用）====================
    flaresolverr_url: str = Field(default="http://localhost:8191", env="FLARESOLVERR_URL")
    use_flaresolverr: bool = Field(default=False, env="USE_FLARESOLVERR")  # 默认禁用，使用Selenium

    # ==================== Selenium配置 ====================
    selenium_headless: bool = Field(default=True, env="SELENIUM_HEADLESS")
    selenium_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        env="SELENIUM_USER_AGENT"
    )
    selenium_page_timeout: int = Field(default=30, env="SELENIUM_PAGE_TIMEOUT")
    use_selenium_mode: bool = Field(default=True, env="USE_SELENIUM_MODE")
    
    def get_database_url(self) -> str:
        """获取完整的数据库连接URL"""
        if self.database_url:
            return self.database_url
        
        return (
            f"postgresql://{self.database_user}:{self.database_password}@"
            f"{self.database_host}:{self.database_port}/{self.database_name}"
            f"?client_encoding=utf8&options=-c%20timezone=Asia/Shanghai"
        )
    
    def get_redis_url(self) -> str:
        """获取完整的Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_cors_origins(self) -> list:
        """获取CORS允许的源列表"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()
