from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
import config
from config import ADMIN_IDS, TRIGGER_PRICE_CHANGE_PERCENT, TRIGGER_TIMEFRAME_MINUTES
from database import async_session, User, News, select, func
from keyboards import admin_keyboard
import logging
import asyncio

router = Router()
logger = logging.getLogger(__name__)

class AdminSettings(StatesGroup):
    waiting_for_price_change = State()
    waiting_for_timeframe = State()
    waiting_for_broadcast = State()
    waiting_for_channel_post = State()

# Middleware для проверки админства будет применен в bot.py

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    # Проверяем, админ ли пользователь
    if message.from_user.id not in ADMIN_IDS:
        # Дополнительно проверим в БД
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
            if not user or not user.is_admin:
                await message.answer("⛔ Доступ запрещен.")
                return
    text = (
        "🔐 **Панель администратора**\n\n"
        "**Текущие настройки триггера:**\n"
        f"• Изменение цены: {config.TRIGGER_PRICE_CHANGE_PERCENT}%\n"
        f"• Таймфрейм: {config.TRIGGER_TIMEFRAME_MINUTES} мин.\n\n"
        "**Действия:**"
    )
    await message.answer(text, reply_markup=admin_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        news_count = await session.scalar(select(func.count(News.id)))
        triggered_count = await session.scalar(select(func.count(News.id)).where(News.triggered == True))
    text = (
        f"📊 **Статистика бота**\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📰 Всего новостей в БД: {news_count}\n"
        f"⚡ Триггерных новостей: {triggered_count}\n"
        f"📈 Текущий порог триггера: {config.TRIGGER_PRICE_CHANGE_PERCENT}% за {config.TRIGGER_TIMEFRAME_MINUTES} мин."
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    await callback.message.edit_text("Введите новый порог изменения цены (в процентах, например 2.5):")
    await state.set_state(AdminSettings.waiting_for_price_change)
    await callback.answer()

@router.message(AdminSettings.waiting_for_price_change)
async def process_price_change(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещен.")
        await state.clear()
        return
    try:
        new_value = float(message.text)
        config.TRIGGER_PRICE_CHANGE_PERCENT = new_value
        await message.answer(f"✅ Порог изменения цены установлен: {new_value}%")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")
    finally:
        await state.clear()

@router.callback_query(F.data == "admin_broadcast_all")
async def admin_broadcast_all(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    await callback.message.edit_text("Введите сообщение для рассылки всем пользователям:")
    await state.set_state(AdminSettings.waiting_for_broadcast)
    await callback.answer()

@router.message(AdminSettings.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещен.")
        await state.clear()
        return
    from bot import bot
    text = message.text
    async with async_session() as session:
        users = await session.execute(select(User.telegram_id))
        user_ids = [row[0] for row in users]
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, f"📢 **Объявление:**\n{text}", parse_mode=ParseMode.MARKDOWN)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение {uid}: {e}")
    await message.answer(f"✅ Рассылка завершена. Отправлено {sent} пользователям.")
    await state.clear()

@router.callback_query(F.data == "admin_broadcast_channel")
async def admin_broadcast_channel(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    await callback.message.edit_text("Введите сообщение для публикации в канал:")
    await state.set_state(AdminSettings.waiting_for_channel_post)
    await callback.answer()

@router.message(AdminSettings.waiting_for_channel_post)
async def process_channel_post(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещен.")
        await state.clear()
        return
    from bot import bot
    from config import CHANNEL_ID
    if not CHANNEL_ID:
        await message.answer("❌ CHANNEL_ID не задан в .env")
        return
    try:
        await bot.send_message(CHANNEL_ID, message.text, parse_mode=ParseMode.MARKDOWN)
        await message.answer("✅ Сообщение опубликовано в канале.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()