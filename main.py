"""
YouTube Downloader Bot
Главный файл для запуска бота
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from tortoise import Tortoise

from app.config.settings import settings
from app.handlers import routers
from app.middlewares import AuthMiddleware, RateLimitMiddleware
from app.services.logger import setup_logger, get_logger

# Настраиваем логирование
setup_logger()
logger = get_logger(__name__)


async def init_database():
    """Инициализация базы данных"""
    try:
        # Используем единую конфигурацию базы данных
        from db_config import TORTOISE_ORM
        
        await Tortoise.init(
            config=TORTOISE_ORM
        )
        
        # Генерируем схемы только если это не продакшн
        # В продакшне используйте aerich миграции
        await Tortoise.generate_schemas()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise


async def close_database():
    """Закрытие соединения с базой данных"""
    await Tortoise.close_connections()
    logger.info("Соединение с базой данных закрыто")


async def main():
    """Главная функция"""
    
    logger.info("🚀 Запуск YouTube Downloader Bot")
    
    # Создаем папку для скачиваний
    download_path = Path(settings.download_path)
    download_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Папка для скачиваний: {download_path.absolute()}")
    
    # Инициализируем базу данных
    await init_database()
    
    # Создаем бота и диспетчер
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Регистрируем миддлвары
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    
    # Регистрируем роутеры
    for router in routers:
        dp.include_router(router)
    
    logger.info(f"Зарегистрировано роутеров: {len(routers)}")
    
    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"Бот запущен: @{bot_info.username} ({bot_info.full_name})")
        
        # Проверяем администраторов
        if settings.admin_ids:
            logger.info(f"Администраторы: {settings.admin_ids}")
            
            # Уведомляем администраторов о запуске
            for admin_id in settings.admin_ids:
                try:
                    await bot.send_message(
                        admin_id,
                        "🟢 <b>Бот запущен!</b>\n\n"
                        f"🤖 <b>Имя:</b> {bot_info.full_name}\n"
                        f"🔗 <b>Username:</b> @{bot_info.username}\n"
                        f"🕐 <b>Время запуска:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                        "Система готова к работе!",
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.warning(f"Не удалось уведомить администратора {admin_id}: {e}")
        
        # Запускаем поллинг
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        # Закрываем соединения
        await bot.session.close()
        await close_database()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        # Проверяем версию Python
        if sys.version_info < (3, 11):
            print("❌ Требуется Python 3.11 или выше")
            sys.exit(1)
        
        # Проверяем наличие токена
        if not settings.bot_token:
            print("❌ Не указан токен бота в переменной BOT_TOKEN")
            print("💡 Создайте файл .env с настройками или запустите: python init_aerich.py")
            sys.exit(1)
        
        # Запускаем бота
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
