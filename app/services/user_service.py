"""
Сервис для работы с пользователями
"""
from typing import Optional, List
from datetime import datetime, timedelta
from aiogram.types import User as TelegramUser
from tortoise.queryset import Q
from tortoise.exceptions import DoesNotExist

from app.models import User, DownloadHistory
from app.config.settings import settings
from app.services.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """Сервис для работы с пользователями"""
    
    @staticmethod
    async def get_or_create_user(telegram_user: TelegramUser) -> User:
        """Получает или создает пользователя"""
        try:
            user = await User.get(telegram_id=telegram_user.id)
            
            # Обновляем информацию пользователя
            updated = False
            if user.username != telegram_user.username:
                user.username = telegram_user.username
                updated = True
            if user.first_name != telegram_user.first_name:
                user.first_name = telegram_user.first_name
                updated = True
            if user.last_name != telegram_user.last_name:
                user.last_name = telegram_user.last_name
                updated = True
            if user.language_code != telegram_user.language_code:
                user.language_code = telegram_user.language_code
                updated = True
            
            if updated:
                await user.save()
                
            await user.update_activity()
            
        except DoesNotExist:
            # Создаем нового пользователя
            is_admin = telegram_user.id in settings.admin_ids
            
            user = await User.create(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                is_admin=is_admin,
                last_activity=datetime.utcnow()
            )
            
            logger.info(f"Создан новый пользователь: {user}")
            
        return user
    
    @staticmethod
    async def is_user_blocked(telegram_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        try:
            user = await User.get(telegram_id=telegram_id)
            return user.is_blocked
        except DoesNotExist:
            return False
    
    @staticmethod
    async def block_user(telegram_id: int) -> bool:
        """Блокирует пользователя"""
        try:
            user = await User.get(telegram_id=telegram_id)
            user.is_blocked = True
            await user.save()
            logger.info(f"Пользователь {telegram_id} заблокирован")
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    async def unblock_user(telegram_id: int) -> bool:
        """Разблокирует пользователя"""
        try:
            user = await User.get(telegram_id=telegram_id)
            user.is_blocked = False
            await user.save()
            logger.info(f"Пользователь {telegram_id} разблокирован")
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    async def get_user_stats(telegram_id: int) -> Optional[dict]:
        """Получает статистику пользователя"""
        try:
            user = await User.get(telegram_id=telegram_id).prefetch_related("download_history")
            
            # Статистика за сегодня
            today = datetime.utcnow().date()
            today_downloads = await DownloadHistory.filter(
                user=user,
                created_at__gte=today
            ).count()
            
            # Статистика за неделю
            week_ago = datetime.utcnow() - timedelta(days=7)
            week_downloads = await DownloadHistory.filter(
                user=user,
                created_at__gte=week_ago
            ).count()
            
            # Последнее скачивание
            last_download = await DownloadHistory.filter(user=user).first()
            
            return {
                "user_id": user.telegram_id,
                "username": user.username,
                "full_name": user.full_name,
                "total_downloads": user.total_downloads,
                "total_download_size": user.total_download_size,
                "today_downloads": today_downloads,
                "week_downloads": week_downloads,
                "last_download": last_download.created_at if last_download else None,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
                "last_activity": user.last_activity
            }
            
        except DoesNotExist:
            return None
    
    @staticmethod
    async def get_all_users(
        limit: int = 100,
        offset: int = 0,
        search: str = None
    ) -> List[User]:
        """Получает список всех пользователей"""
        query = User.all()
        
        if search:
            query = query.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return await query.offset(offset).limit(limit).order_by("-created_at")
    
    @staticmethod
    async def get_admin_users() -> List[User]:
        """Получает список администраторов"""
        return await User.filter(is_admin=True)
    
    @staticmethod
    async def promote_to_admin(telegram_id: int) -> bool:
        """Делает пользователя администратором"""
        try:
            user = await User.get(telegram_id=telegram_id)
            user.is_admin = True
            await user.save()
            logger.info(f"Пользователь {telegram_id} повышен до администратора")
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    async def demote_from_admin(telegram_id: int) -> bool:
        """Снимает права администратора"""
        try:
            user = await User.get(telegram_id=telegram_id)
            user.is_admin = False
            await user.save()
            logger.info(f"У пользователя {telegram_id} сняты права администратора")
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    async def get_users_count() -> int:
        """Получает общее количество пользователей"""
        return await User.all().count()
    
    @staticmethod
    async def get_active_users_count(days: int = 7) -> int:
        """Получает количество активных пользователей за период"""
        since = datetime.utcnow() - timedelta(days=days)
        return await User.filter(last_activity__gte=since).count() 