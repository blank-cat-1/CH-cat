#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接管理
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.get_database_url(),
    echo=False,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={
        "options": "-c statement_timeout=30000"
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话 - FastAPI依赖注入使用"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话 - 上下文管理器方式"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"数据库操作失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_db_session() -> Session:
    """创建数据库会话 - 手动管理方式"""
    return SessionLocal()


def get_engine():
    """获取数据库引擎"""
    return engine


def check_db_health() -> bool:
    """检查数据库连接健康状态"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False


def init_database():
    """初始化数据库，创建所有表"""
    from models import import_all_models
    
    # 导入所有模型
    import_all_models()
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库初始化完成，所有表已创建")
