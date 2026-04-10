# API Routes模块

from .auth import router as auth_router
from .subscription import router as subscription_router
from .crawler import router as crawler_router
from .magnet import router as magnet_router
from .search import router as search_router
from .settings import router as settings_router
from .emby import router as emby_router
from .telegram import router as telegram_router
from .notification import router as notification_router
from .health import router as health_router
from .checkin import router as checkin_router

__all__ = [
    "auth_router",
    "subscription_router",
    "crawler_router",
    "magnet_router",
    "search_router",
    "settings_router",
    "emby_router",
    "telegram_router",
    "notification_router",
    "health_router",
    "checkin_router",
]
