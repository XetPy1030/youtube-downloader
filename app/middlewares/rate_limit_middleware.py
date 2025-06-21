"""
Миддлвар для ограничения частоты запросов
"""
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message

from app.config.settings import settings
from app.services.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Миддлвар для ограничения частоты запросов"""
    
    def __init__(self):
        self.user_requests = {}  # Хранилище запросов пользователей
        self.cleanup_interval = 60  # Интервал очистки в секундах
        self.last_cleanup = time.time()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Получаем пользователя из события
        user_id = None
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
            elif event.inline_query:
                user_id = event.inline_query.from_user.id
        
        if user_id:
            # Проверяем администраторов (для них нет ограничений)
            if user_id in settings.admin_ids:
                return await handler(event, data)
            
            current_time = time.time()
            
            # Очищаем старые записи
            if current_time - self.last_cleanup > self.cleanup_interval:
                await self._cleanup_old_requests(current_time)
                self.last_cleanup = current_time
            
            # Проверяем лимит для пользователя
            if await self._check_rate_limit(user_id, current_time):
                return await handler(event, data)
            else:
                logger.warning(f"Пользователь {user_id} превысил лимит запросов")
                # Можно отправить сообщение о превышении лимита
                if isinstance(event, Update) and event.message:
                    await event.message.answer(
                        "⚠️ Вы превысили лимит запросов. Попробуйте позже."
                    )
                return
        
        return await handler(event, data)
    
    async def _check_rate_limit(self, user_id: int, current_time: float) -> bool:
        """Проверяет лимит запросов для пользователя"""
        window_start = current_time - 60  # Окно в 1 минуту
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Удаляем старые запросы
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > window_start
        ]
        
        # Проверяем лимит
        if len(self.user_requests[user_id]) >= settings.rate_limit_requests:
            return False
        
        # Добавляем текущий запрос
        self.user_requests[user_id].append(current_time)
        return True
    
    async def _cleanup_old_requests(self, current_time: float) -> None:
        """Очищает старые запросы"""
        window_start = current_time - 60
        
        for user_id in list(self.user_requests.keys()):
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if req_time > window_start
            ]
            
            # Удаляем пустые записи
            if not self.user_requests[user_id]:
                del self.user_requests[user_id] 