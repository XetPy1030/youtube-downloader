"""
Хендлеры для скачивания видео
"""
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from app.models import User
from app.services.youtube_service import YouTubeService
from app.services.logger import get_logger

logger = get_logger(__name__)
router = Router()

# Инициализируем сервис YouTube
youtube_service = YouTubeService()


@router.message(F.text.regexp(r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)'))
async def youtube_url_handler(message: Message, user: User):
    """Обработчик YouTube ссылок"""
    url = message.text.strip()
    
    # Проверяем валидность URL
    if not youtube_service.is_valid_youtube_url(url):
        await message.answer(
            "❌ Неверная ссылка на YouTube видео.\n"
            "Поддерживаемые форматы:\n"
            "• https://youtube.com/watch?v=VIDEO_ID\n"
            "• https://youtu.be/VIDEO_ID"
        )
        return
    
    # Отправляем сообщение о загрузке
    loading_msg = await message.answer("🔍 Получаем информацию о видео...")
    
    try:
        # Получаем или создаем видео в базе данных
        video = await youtube_service.get_or_create_video(url)
        
        if not video:
            await loading_msg.edit_text(
                "❌ Не удалось получить информацию о видео.\n"
                "Проверьте ссылку и попробуйте еще раз."
            )
            return
        
        # Создаем сообщение с информацией о видео
        view_count_text = f"{video.view_count:,}" if video.view_count else 'Неизвестно'
        info_text = f"""
🎬 <b>{video.title}</b>

📺 <b>Канал:</b> {video.channel_name or 'Неизвестно'}
⏱ <b>Длительность:</b> {video.duration_formatted or 'Неизвестно'}
👁 <b>Просмотры:</b> {view_count_text}
📅 <b>Дата загрузки:</b> {video.upload_date.strftime('%d.%m.%Y') if video.upload_date else 'Неизвестно'}

Выберите качество и формат для скачивания:
        """
        
        # Создаем клавиатуру с вариантами скачивания
        builder = InlineKeyboardBuilder()
        
        # Получаем доступные качества
        qualities = await youtube_service.get_available_qualities(video)
        
        if qualities:
            # Добавляем кнопки для разных качеств MP4
            for quality in qualities[:5]:  # Ограничиваем до 5 качеств
                builder.button(
                    text=f"📹 {quality['name']} MP4",
                    callback_data=f"download:{video.id}:mp4:{quality['name']}"
                )
        else:
            # Добавляем стандартные варианты
            builder.button(
                text="📹 720p MP4",
                callback_data=f"download:{video.id}:mp4:720p"
            )
            builder.button(
                text="📹 480p MP4",
                callback_data=f"download:{video.id}:mp4:480p"
            )
            builder.button(
                text="📹 360p MP4",
                callback_data=f"download:{video.id}:mp4:360p"
            )
        
        # Добавляем вариант MP3
        builder.button(
            text="🎵 MP3 (только аудио)",
            callback_data=f"download:{video.id}:mp3:audio"
        )
        
        # Добавляем кнопку с информацией
        builder.button(
            text="ℹ️ Подробная информация",
            callback_data=f"info:{video.id}"
        )
        
        builder.adjust(2, 1, 1)  # 2 кнопки в первых рядах, потом по 1
        
        await loading_msg.edit_text(
            info_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки YouTube URL {url}: {e}")
        await loading_msg.edit_text(
            "❌ Произошла ошибка при обработке видео.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


@router.callback_query(F.data.startswith("download:"))
async def download_callback(callback: CallbackQuery, user: User):
    """Обработчик скачивания видео"""
    try:
        _, video_id, format_type, quality = callback.data.split(":")
        video_id = int(video_id)
        
        # Получаем видео из базы данных
        from app.models import Video
        video = await Video.get(id=video_id)
        
        await callback.answer("🚀 Начинаем скачивание...")
        
        # Обновляем сообщение
        await callback.message.edit_text(
            f"⏳ Скачиваем видео: <b>{video.title}</b>\n"
            f"📹 Качество: {quality}\n"
            f"📁 Формат: {format_type.upper()}\n\n"
            "Это может занять некоторое время...",
            parse_mode="HTML"
        )
        
        # Скачиваем видео
        download_record = await youtube_service.download_video(
            video=video,
            user=user,
            quality=quality,
            format_type=format_type
        )
        
        if download_record and download_record.is_completed:
            # Отправляем файл пользователю
            if download_record.file_path and os.path.exists(download_record.file_path):
                try:
                    # Создаем объект файла
                    file = FSInputFile(
                        download_record.file_path,
                        filename=f"{video.title[:50]}.{format_type}"
                    )
                    
                    # Отправляем файл
                    if format_type == "mp3":
                        sent_message = await callback.message.answer_audio(
                            file,
                            caption=f"🎵 <b>{video.title}</b>\n📺 {video.channel_name}",
                            parse_mode="HTML"
                        )
                    else:
                        sent_message = await callback.message.answer_video(
                            file,
                            caption=f"🎬 <b>{video.title}</b>\n📺 {video.channel_name}",
                            parse_mode="HTML"
                        )
                    
                    # Сохраняем file_id для повторного использования
                    if format_type == "mp3" and sent_message.audio:
                        download_record.telegram_file_id = sent_message.audio.file_id
                    elif sent_message.video:
                        download_record.telegram_file_id = sent_message.video.file_id
                    
                    await download_record.save(update_fields=["telegram_file_id"])
                    
                    # Обновляем сообщение об успехе
                    await callback.message.edit_text(
                        f"✅ <b>Скачивание завершено!</b>\n\n"
                        f"🎬 <b>Видео:</b> {video.title}\n"
                        f"📹 <b>Качество:</b> {quality}\n"
                        f"📁 <b>Формат:</b> {format_type.upper()}\n"
                        f"💾 <b>Размер:</b> {video.file_size_formatted or 'Неизвестно'}",
                        parse_mode="HTML"
                    )
                    
                except TelegramBadRequest as e:
                    logger.error(f"Ошибка отправки файла: {e}")
                    await callback.message.edit_text(
                        "❌ Файл слишком большой для отправки через Telegram.\n"
                        "Попробуйте выбрать более низкое качество."
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки файла: {e}")
                    await callback.message.edit_text(
                        "❌ Ошибка при отправке файла.\n"
                        "Попробуйте позже."
                    )
            else:
                await callback.message.edit_text(
                    "❌ Файл не найден на сервере.\n"
                    "Попробуйте скачать заново."
                )
        else:
            # Скачивание провалилось
            error_msg = download_record.error_message if download_record else "Неизвестная ошибка"
            await callback.message.edit_text(
                f"❌ <b>Ошибка скачивания:</b>\n{error_msg}\n\n"
                "Попробуйте:\n"
                "• Выбрать другое качество\n"
                "• Проверить ссылку\n"
                "• Повторить попытку позже"
            )
        
    except Exception as e:
        logger.error(f"Ошибка в download_callback: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при скачивании.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


@router.callback_query(F.data.startswith("info:"))
async def info_callback(callback: CallbackQuery, user: User):
    """Обработчик получения подробной информации о видео"""
    try:
        _, video_id = callback.data.split(":")
        video_id = int(video_id)
        
        from app.models import Video
        video = await Video.get(id=video_id)
        
        # Формируем подробную информацию
        info_text = f"""
🎬 <b>{video.title}</b>

📺 <b>Канал:</b> {video.channel_name or 'Неизвестно'}
🆔 <b>ID канала:</b> <code>{video.channel_id or 'Неизвестно'}</code>
⏱ <b>Длительность:</b> {video.duration_formatted or 'Неизвестно'}
👁 <b>Просмотры:</b> {f"{video.view_count:,}" if video.view_count else 'Неизвестно'}
👍 <b>Лайки:</b> {f"{video.like_count:,}" if video.like_count else 'Неизвестно'}
📅 <b>Дата загрузки:</b> {video.upload_date.strftime('%d.%m.%Y') if video.upload_date else 'Неизвестно'}
📊 <b>Скачиваний:</b> {video.download_count}

🔗 <b>Ссылка:</b> <a href="{video.youtube_url}">Открыть на YouTube</a>
        """
        
        if video.description:
            # Обрезаем описание до 500 символов
            desc = video.description[:500] + "..." if len(video.description) > 500 else video.description
            info_text += f"\n📝 <b>Описание:</b>\n{desc}"
        
        # Кнопка назад
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад к скачиванию", callback_data=f"back_to_download:{video.id}")
        
        await callback.message.edit_text(
            info_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка в info_callback: {e}")
        await callback.answer("❌ Ошибка получения информации", show_alert=True)


@router.callback_query(F.data.startswith("back_to_download:"))
async def back_to_download_callback(callback: CallbackQuery, user: User):
    """Возврат к выбору скачивания"""
    try:
        _, video_id = callback.data.split(":")
        video_id = int(video_id)
        
        from app.models import Video
        video = await Video.get(id=video_id)
        
        # Воссоздаем исходное сообщение
        info_text = f"""
🎬 <b>{video.title}</b>

📺 <b>Канал:</b> {video.channel_name or 'Неизвестно'}
⏱ <b>Длительность:</b> {video.duration_formatted or 'Неизвестно'}
👁 <b>Просмотры:</b> {f"{video.view_count:,}" if video.view_count else 'Неизвестно'}
📅 <b>Дата загрузки:</b> {video.upload_date.strftime('%d.%m.%Y') if video.upload_date else 'Неизвестно'}

Выберите качество и формат для скачивания:
        """
        
        # Воссоздаем клавиатуру
        builder = InlineKeyboardBuilder()
        
        qualities = await youtube_service.get_available_qualities(video)
        
        if qualities:
            for quality in qualities[:5]:
                builder.button(
                    text=f"📹 {quality['name']} MP4",
                    callback_data=f"download:{video.id}:mp4:{quality['name']}"
                )
        else:
            builder.button(text="📹 720p MP4", callback_data=f"download:{video.id}:mp4:720p")
            builder.button(text="📹 480p MP4", callback_data=f"download:{video.id}:mp4:480p")
            builder.button(text="📹 360p MP4", callback_data=f"download:{video.id}:mp4:360p")
        
        builder.button(text="🎵 MP3 (только аудио)", callback_data=f"download:{video.id}:mp3:audio")
        builder.button(text="ℹ️ Подробная информация", callback_data=f"info:{video.id}")
        builder.adjust(2, 1, 1)
        
        await callback.message.edit_text(
            info_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в back_to_download_callback: {e}")
        await callback.answer("❌ Ошибка", show_alert=True) 