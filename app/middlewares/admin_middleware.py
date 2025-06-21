from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.types import TelegramObject, Message, CallbackQuery, Update

from app.services.logger import get_logger

logger = get_logger(__name__)


class AdminMiddleware(BaseMiddleware):
    """Миддлвар, проверяющий является ли пользователь администратором."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Извлекаем пользователя, который был уже добавлен AuthMiddleware
        db_user = data.get("user")

        # Если пользователь отсутствует или не является администратором — запрещаем доступ
        if not db_user or not db_user.is_admin:
            # Пытаемся корректно сообщить об ошибке в зависимости от типа события
            if isinstance(event, Message):
                await event.answer("❌ У вас нет прав администратора")
            elif isinstance(event, CallbackQuery):
                # Для callback покажем алерт, чтобы сообщение отобразилось поверх интерфейса
                await event.answer("❌ У вас нет прав администратора", show_alert=True)
            else:
                logger.warning("Событие без поддержки ответа в AdminMiddleware: %s", type(event))
            # Прерываем дальнейшую обработку
            raise CancelHandler()

        # Всё в порядке, продолжаем цепочку
        return await handler(event, data)
