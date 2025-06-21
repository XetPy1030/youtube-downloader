"""
Хендлеры для администраторов
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import User
from app.services.user_service import UserService
from app.services.youtube_service import YouTubeService
from app.services.logger import get_logger
from app.middlewares import AdminMiddleware

logger = get_logger(__name__)
router = Router()

# Инициализируем сервисы
user_service = UserService()
youtube_service = YouTubeService()

router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())


@router.message(Command("admin"))
async def admin_panel(message: Message, user: User):
    """Главная панель администратора"""
    
    # Получаем статистику
    stats = await youtube_service.get_download_stats()
    users_count = await user_service.get_users_count()
    active_users = await user_service.get_active_users_count()
    
    admin_text = f"""
👑 <b>Панель администратора</b>

📊 <b>Статистика:</b>
• 👥 Всего пользователей: {users_count}
• 🟢 Активных за неделю: {active_users}
• 📥 Всего скачиваний: {stats['total_downloads']}
• ✅ Успешных: {stats['completed_downloads']}
• ❌ Ошибок: {stats['failed_downloads']}
• 📈 Успешность: {stats['success_rate']:.1f}%
• 📅 Сегодня: {stats['today_downloads']}

Выберите действие:
    """
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи", callback_data="admin_users")
    builder.button(text="📊 Подробная статистика", callback_data="admin_stats")
    builder.button(text="📹 Популярные видео", callback_data="admin_videos")
    builder.button(text="🧹 Очистка файлов", callback_data="admin_cleanup")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="⚙️ Настройки", callback_data="admin_settings")
    builder.adjust(2)
    
    await message.answer(
        admin_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery, user: User):
    """Управление пользователями"""
    
    users = await user_service.get_all_users(limit=20)
    users_count = await user_service.get_users_count()
    
    users_text = f"👥 <b>Пользователи</b> (показано 20 из {users_count})\n\n"
    
    for u in users:
        status = "👑" if u.is_admin else "🚫" if u.is_blocked else "👤"
        users_text += f"{status} <b>{u.full_name}</b> (@{u.username or 'нет'})\n"
        users_text += f"    ID: <code>{u.telegram_id}</code> | Скачиваний: {u.total_downloads}\n"
        users_text += f"    Регистрация: {u.created_at.strftime('%d.%m.%Y')}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Найти пользователя", callback_data="admin_user_search")
    builder.button(text="📊 Топ пользователей", callback_data="admin_user_top")
    builder.button(text="🚫 Заблокированные", callback_data="admin_user_blocked")
    builder.button(text="◀️ Назад", callback_data="admin_back")
    builder.adjust(1)
    
    await callback.message.edit_text(
        users_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery, user: User):
    """Подробная статистика"""
    
    stats = await youtube_service.get_download_stats()
    
    stats_text = f"""
📊 <b>Подробная статистика</b>

📥 <b>Скачивания:</b>
• Всего: {stats['total_downloads']}
• Успешных: {stats['completed_downloads']}
• Ошибок: {stats['failed_downloads']}
• Успешность: {stats['success_rate']:.1f}%
• Сегодня: {stats['today_downloads']}

🎬 <b>Популярные видео:</b>
    """
    
    for i, video in enumerate(stats['popular_videos'][:5], 1):
        stats_text += f"{i}. {video['title'][:50]}...\n"
        stats_text += f"   Скачиваний: {video['download_count']}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📈 Экспорт статистики", callback_data="admin_export_stats")
    builder.button(text="◀️ Назад", callback_data="admin_back")
    builder.adjust(1)
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_cleanup")
async def admin_cleanup_callback(callback: CallbackQuery, user: User):
    """Очистка файлов"""
    
    await callback.answer("🧹 Очищаем старые файлы...")
    
    try:
        cleaned_count = await youtube_service.cleanup_old_files()
        
        cleanup_text = f"""
🧹 <b>Очистка завершена</b>

✅ Удалено файлов: {cleaned_count}
📁 Освобождено место на диске

Файлы старше 7 дней были удалены.
        """
        
    except Exception as e:
        logger.error(f"Ошибка очистки файлов: {e}")
        cleanup_text = "❌ Ошибка при очистке файлов"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    
    await callback.message.edit_text(
        cleanup_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, user: User):
    """Рассылка сообщений"""
    
    broadcast_text = """
📢 <b>Рассылка сообщений</b>

Для отправки рассылки используйте команду:
<code>/broadcast ваше_сообщение</code>

Сообщение будет отправлено всем активным пользователям.

⚠️ <b>Внимание:</b> Используйте рассылку осторожно!
    """
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    
    await callback.message.edit_text(
        broadcast_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.message(Command("broadcast"))
async def broadcast_command(message: Message, user: User):
    """Команда рассылки"""
    
    # Получаем текст сообщения
    text_parts = message.text.split(' ', 1)
    if len(text_parts) < 2:
        await message.answer("❌ Укажите текст для рассылки:\n<code>/broadcast ваше_сообщение</code>", parse_mode="HTML")
        return
    
    broadcast_text = text_parts[1]
    
    # Получаем всех активных пользователей
    users = await user_service.get_all_users(limit=1000)
    
    await message.answer(f"📢 Начинаем рассылку для {len(users)} пользователей...")
    
    sent_count = 0
    failed_count = 0
    
    for target_user in users:
        if target_user.is_blocked:
            continue
        
        try:
            await message.bot.send_message(
                target_user.telegram_id,
                f"📢 <b>Сообщение от администрации:</b>\n\n{broadcast_text}",
                parse_mode="HTML"
            )
            sent_count += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {target_user.telegram_id}: {e}")
            failed_count += 1
    
    await message.answer(
        f"✅ Рассылка завершена!\n"
        f"📤 Отправлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}"
    )


@router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: CallbackQuery, user: User):
    """Возврат к главной панели администратора"""
    
    # Получаем обновленную статистику
    stats = await youtube_service.get_download_stats()
    users_count = await user_service.get_users_count()
    active_users = await user_service.get_active_users_count()
    
    admin_text = f"""
👑 <b>Панель администратора</b>

📊 <b>Статистика:</b>
• 👥 Всего пользователей: {users_count}
• 🟢 Активных за неделю: {active_users}
• 📥 Всего скачиваний: {stats['total_downloads']}
• ✅ Успешных: {stats['completed_downloads']}
• ❌ Ошибок: {stats['failed_downloads']}
• 📈 Успешность: {stats['success_rate']:.1f}%
• 📅 Сегодня: {stats['today_downloads']}

Выберите действие:
    """
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи", callback_data="admin_users")
    builder.button(text="📊 Подробная статистика", callback_data="admin_stats")
    builder.button(text="📹 Популярные видео", callback_data="admin_videos")
    builder.button(text="🧹 Очистка файлов", callback_data="admin_cleanup")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="⚙️ Настройки", callback_data="admin_settings")
    builder.adjust(2)
    
    await callback.message.edit_text(
        admin_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


# Команды для управления пользователями
@router.message(Command("ban"))
async def ban_user_command(message: Message, user: User):
    """Команда блокировки пользователя"""
    
    # Получаем ID пользователя
    text_parts = message.text.split(' ', 1)
    if len(text_parts) < 2:
        await message.answer("❌ Укажите ID пользователя:\n<code>/ban user_id</code>", parse_mode="HTML")
        return
    
    try:
        target_user_id = int(text_parts[1])
        success = await user_service.block_user(target_user_id)
        
        if success:
            await message.answer(f"✅ Пользователь {target_user_id} заблокирован")
        else:
            await message.answer(f"❌ Пользователь {target_user_id} не найден")
            
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")


@router.message(Command("unban"))
async def unban_user_command(message: Message, user: User):
    """Команда разблокировки пользователя"""
    
    # Получаем ID пользователя
    text_parts = message.text.split(' ', 1)
    if len(text_parts) < 2:
        await message.answer("❌ Укажите ID пользователя:\n<code>/unban user_id</code>", parse_mode="HTML")
        return
    
    try:
        target_user_id = int(text_parts[1])
        success = await user_service.unblock_user(target_user_id)
        
        if success:
            await message.answer(f"✅ Пользователь {target_user_id} разблокирован")
        else:
            await message.answer(f"❌ Пользователь {target_user_id} не найден")
            
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя") 