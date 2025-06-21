"""
Настройки приложения
"""
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Telegram Bot
    bot_token: str = Field(..., description="Токен Telegram бота")
    admin_ids: List[int] = Field(default_factory=list, description="ID администраторов")
    
    # Database
    database_url: str = Field(
        default="postgres://user:password@localhost:5432/youtube_bot",
        description="URL подключения к базе данных"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="URL подключения к Redis"
    )
    
    # YouTube Download
    download_path: str = Field(
        default="./downloads",
        description="Путь для сохранения скачанных видео"
    )
    max_video_duration: int = Field(
        default=3600,  # 1 час
        description="Максимальная длительность видео в секундах"
    )
    max_file_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="Максимальный размер файла в байтах"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Уровень логирования")
    log_file: str = Field(default="bot.log", description="Файл логов")
    
    # Rate limiting
    rate_limit_requests: int = Field(
        default=5,
        description="Количество запросов в минуту на пользователя"
    )
    
    @field_validator('admin_ids', mode='before')
    @classmethod
    def parse_admin_ids(cls, value: Union[str, int, List[int]]) -> List[int]:
        """Парсинг ID администраторов из строки или числа в список"""
        if isinstance(value, str):
            # Если строка, разделяем по запятым и преобразуем в числа
            return [int(x.strip()) for x in value.split(',') if x.strip().isdigit()]
        elif isinstance(value, int):
            # Если одно число, делаем из него список
            return [value]
        elif isinstance(value, list):
            # Если уже список, возвращаем как есть
            return value
        else:
            return []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Игнорировать неизвестные переменные из .env


# Глобальный экземпляр настроек
settings = Settings()
