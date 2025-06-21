"""
Модель истории скачиваний
"""
from enum import Enum
from tortoise.models import Model
from tortoise import fields


class DownloadStatus(str, Enum):
    """Статусы скачивания"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadHistory(Model):
    """Модель истории скачиваний"""
    
    id = fields.IntField(pk=True)
    
    # Связи
    user = fields.ForeignKeyField(
        "models.User",
        related_name="download_history",
        description="Пользователь"
    )
    video = fields.ForeignKeyField(
        "models.Video",
        related_name="download_history",
        description="Видео"
    )
    
    # Статус и детали
    status = fields.CharEnumField(
        DownloadStatus,
        default=DownloadStatus.PENDING,
        description="Статус скачивания"
    )
    quality = fields.CharField(max_length=50, null=True, description="Выбранное качество")
    format_type = fields.CharField(max_length=20, default="mp4", description="Тип формата")
    file_size = fields.BigIntField(null=True, description="Размер файла в байтах")
    download_speed = fields.FloatField(null=True, description="Скорость скачивания в Мб/с")
    
    # Пути и файлы
    file_path = fields.TextField(null=True, description="Путь к скачанному файлу")
    telegram_file_id = fields.CharField(max_length=255, null=True, description="ID файла в Telegram")
    
    # Ошибки и дополнительная информация
    error_message = fields.TextField(null=True, description="Сообщение об ошибке")
    metadata = fields.JSONField(null=True, description="Дополнительные метаданные")
    
    # Даты
    created_at = fields.DatetimeField(auto_now_add=True, description="Дата создания")
    started_at = fields.DatetimeField(null=True, description="Дата начала скачивания")
    completed_at = fields.DatetimeField(null=True, description="Дата завершения")
    
    class Meta:
        table = "download_history"
        table_description = "История скачиваний"
        ordering = ["-created_at"]
    
    def __str__(self) -> str:
        return f"Download(user={self.user_id}, video={self.video_id}, status={self.status})"
    
    @property
    def is_completed(self) -> bool:
        """Проверяет, завершено ли скачивание"""
        return self.status == DownloadStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Проверяет, провалилось ли скачивание"""
        return self.status == DownloadStatus.FAILED
    
    @property
    def is_in_progress(self) -> bool:
        """Проверяет, идет ли скачивание"""
        return self.status in [DownloadStatus.PENDING, DownloadStatus.DOWNLOADING]
    
    @property
    def download_time(self) -> float:
        """Возвращает время скачивания в секундах"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    async def mark_as_started(self) -> None:
        """Отмечает скачивание как начатое"""
        from datetime import datetime
        self.status = DownloadStatus.DOWNLOADING
        self.started_at = datetime.utcnow()
        await self.save(update_fields=["status", "started_at"])
    
    async def mark_as_completed(self, file_path: str, file_size: int = None, telegram_file_id: str = None) -> None:
        """Отмечает скачивание как завершенное"""
        from datetime import datetime
        self.status = DownloadStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.file_path = file_path
        if file_size:
            self.file_size = file_size
        if telegram_file_id:
            self.telegram_file_id = telegram_file_id
        await self.save(update_fields=["status", "completed_at", "file_path", "file_size", "telegram_file_id"])
    
    async def mark_as_failed(self, error_message: str) -> None:
        """Отмечает скачивание как проваленное"""
        from datetime import datetime
        self.status = DownloadStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        await self.save(update_fields=["status", "completed_at", "error_message"]) 