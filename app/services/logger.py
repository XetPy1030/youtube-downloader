"""
Настройка логирования
"""
import sys
from pathlib import Path
from loguru import logger
from app.config.settings import settings


def setup_logger() -> None:
    """Настройка системы логирования"""
    
    # Удаляем стандартный хендлер
    logger.remove()
    
    # Настройка формата логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Консольный вывод
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Файловый вывод
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_path,
        format=log_format,
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Отдельный файл для ошибок
    error_log_path = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
    logger.add(
        error_log_path,
        format=log_format,
        level="ERROR",
        rotation="5 MB",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    logger.info("Логирование настроено")


def get_logger(name: str = None):
    """Получение логгера с указанным именем"""
    if name:
        return logger.bind(name=name)
    return logger 