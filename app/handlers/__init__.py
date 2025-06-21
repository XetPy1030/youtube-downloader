"""
Хендлеры бота
"""

from .common import router as common_router
from .download import router as download_router
from .admin import router as admin_router

# Список всех роутеров
routers = [
    common_router,
    download_router,
    admin_router
]

__all__ = ["routers"] 