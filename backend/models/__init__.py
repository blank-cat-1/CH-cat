# Models模块 - 数据模型
from .base import Base
from .magnet import MagnetLink
from .subscription import Subscription
from .post import Post
from .user import User
from .auto_push import AutoPushRule, AutoPushLog
from .cookie import Cookie
from .checkin import CheckInRecord, CheckInConfig, ReplyTemplate
from .system_log import SystemLog

__all__ = [
    "Base",
    "MagnetLink",
    "Subscription",
    "Post",
    "User",
    "AutoPushRule",
    "AutoPushLog",
    "Cookie",
    "CheckInRecord",
    "CheckInConfig",
    "ReplyTemplate",
    "SystemLog",
]




def import_all_models():
    """导入所有模型以确保它们被注册到Base"""
    # 这些导入会触发模型类的执行，从而注册到Base.metadata
    from . import magnet
    from . import subscription
    from . import post
    from . import user
    from . import auto_push
    from . import cookie
    from . import checkin
    from . import system_log
