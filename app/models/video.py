"""
Модель видео
"""
from typing import Optional
from tortoise.models import Model
from tortoise import fields


class Video(Model):
    """Модель видео YouTube"""
    
    id = fields.IntField(pk=True)
    video_id = fields.CharField(max_length=255, unique=True, description="YouTube ID видео")
    title = fields.TextField(description="Название видео")
    description = fields.TextField(null=True, description="Описание видео")
    duration = fields.IntField(null=True, description="Длительность в секундах")
    view_count = fields.BigIntField(null=True, description="Количество просмотров")
    like_count = fields.BigIntField(null=True, description="Количество лайков")
    channel_name = fields.CharField(max_length=255, null=True, description="Название канала")
    channel_id = fields.CharField(max_length=255, null=True, description="ID канала")
    upload_date = fields.DateField(null=True, description="Дата загрузки видео")
    thumbnail_url = fields.TextField(null=True, description="URL превью")
    
    # Технические данные
    available_formats = fields.JSONField(null=True, description="Доступные форматы")
    file_size = fields.BigIntField(null=True, description="Размер файла в байтах")
    quality = fields.CharField(max_length=50, null=True, description="Качество видео")
    format_id = fields.CharField(max_length=50, null=True, description="ID формата")
    
    # Статистика
    download_count = fields.IntField(default=0, description="Количество скачиваний")
    
    # Даты
    created_at = fields.DatetimeField(auto_now_add=True, description="Дата добавления")
    updated_at = fields.DatetimeField(auto_now=True, description="Дата обновления")
    
    # Связи
    download_history: fields.ReverseRelation["DownloadHistory"]
    
    class Meta:
        table = "videos"
        table_description = "YouTube видео"
    
    def __str__(self) -> str:
        return f"Video(video_id={self.video_id}, title={self.title[:50]}...)"
    
    @property
    def youtube_url(self) -> str:
        """Возвращает URL YouTube видео"""
        return f"https://www.youtube.com/watch?v={self.video_id}"
    
    @property
    def duration_formatted(self) -> Optional[str]:
        """Возвращает отформатированную длительность"""
        if not self.duration:
            return None
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_formatted(self) -> Optional[str]:
        """Возвращает отформатированный размер файла"""
        if not self.file_size:
            return None
        
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} ТБ"
    
    async def increment_download_count(self) -> None:
        """Увеличивает счетчик скачиваний"""
        self.download_count += 1
        await self.save(update_fields=["download_count"]) 