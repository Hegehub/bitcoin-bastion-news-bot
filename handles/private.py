from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards import main_menu_keyboard
from metrics import MetricsCollector
from news_analyzer import NewsAnalyzer
from database import get_db, User
import logging

router = Router()
metrics = MetricsCollector()

@router.message(Command("start"))
async def start_private(message: Message, is_admin: bool):
    # Сохраняем пользователя в БД, если его нет
    async for session in get_db():
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(telegram_id=message.from_user.id, username=message.from_user.username)
            session.add(user)
            await session.commit()
    await message.answer(
        "Добро пожаловать в Crypto Analytics Bot!\nВыберите действие:",
        reply_markup=main_menu_keyboard(is_admin)
    )

@router.callback_query(F.data == "btc_price")
async def btc_price_callback(callback: CallbackQuery):
    price_data = await metrics.get_btc_price_coindesk()
    if price_data:
        text = f"💰 BTC Price: ${price_data['price']:,.2f} (source: {price_data['source']})"
    else:
        text = "Не удалось получить цену BTC."
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())

# Другие обработчики для fear_greed, dominance, liquidity...
