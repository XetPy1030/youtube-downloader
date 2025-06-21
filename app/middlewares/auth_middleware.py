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
        user = None
        if isinstance(event, Update):
            if event.message:
                user = event.message.from_user
            elif event.callback_query:
                user = event.callback_query.from_user
            elif event.inline_query:
                user = event.inline_query.from_user
        
        if user:
            # Проверяем, не заблокирован ли пользователь
            if await UserService.is_user_blocked(user.id):
                logger.warning(f"Заблокированный пользователь {user.id} пытался использовать бота")
                return
            
            # Получаем или создаем пользователя в базе данных
            db_user = await UserService.get_or_create_user(user)
            data["user"] = db_user
            data["telegram_user"] = user
            
            logger.debug(f"Пользователь {user.id} аутентифицирован")
        
        return await handler(event, data) 