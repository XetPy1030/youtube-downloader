"""
Миддлвар для аутентификации
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message

from app.services.user_service import UserService
from app.services.logger import get_logger

logger = get_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Миддлвар для аутентификации и создания пользователей"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Получаем пользователя из события
        telegram_user = None
        
        # Если это напрямую Message/CallbackQuery и т.д.
        if hasattr(event, 'from_user'):
            telegram_user = event.from_user
        # Если это Update объект
        elif isinstance(event, Update):
            if event.message:
                telegram_user = event.message.from_user
            elif event.callback_query:
                telegram_user = event.callback_query.from_user
            elif event.inline_query:
                telegram_user = event.inline_query.from_user
        
        if telegram_user:
            # Проверяем, не заблокирован ли пользователь
            if await UserService.is_user_blocked(telegram_user.id):
                logger.warning(f"Заблокированный пользователь {telegram_user.id} пытался использовать бота")
                return
            
            # Получаем или создаем пользователя в базе данных
            db_user = await UserService.get_or_create_user(telegram_user)
            data["user"] = db_user
            data["telegram_user"] = telegram_user
            
            logger.debug(f"Пользователь {telegram_user.id} аутентифицирован")
        
        return await handler(event, data) 