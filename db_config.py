"""
Конфигурация базы данных для YouTube Downloader Bot

Используется как для Aerich миграций, так и для основного приложения.
Единая точка конфигурации Tortoise ORM.
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgres://user:password@localhost:5432/youtube_bot"
)

# Конфигурация Tortoise ORM
TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL
    },
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "UTC"
} 