from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from services.api_client import api_client
from redis_cache import get_cache, set_cache
from database import add_user, async_session, User, select
from keyboards import main_keyboard, subscription_keyboard
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    text = (
        "👋 Привет! Я бот крипто-аналитики.\n\n"
        "Я получаю новости в реальном времени и определяю, какие из них вызвали движение цены. "
        "Такие новости публикуются в канале.\n\n"
        "Используйте кнопки ниже для быстрого доступа к функциям."
    )
    await message.answer(text, reply_markup=main_keyboard())

# Обработчики текстовых кнопок (вызывают соответствующие команды)
@router.message(F.text == "📰 Последние новости")
async def button_latest(message: Message):
    await cmd_latest(message)

@router.message(F.text == "💰 Цена BTC")
async def button_btc(message: Message):
    await cmd_btc(message)

@router.message(F.text == "😨 Индекс страха")
async def button_feargreed(message: Message):
    await cmd_feargreed(message)

@router.message(F.text == "🐋 Киты")
async def button_whales(message: Message):
    await cmd_whales(message)

@router.message(F.text == "💥 Ликвидации")
async def button_liquidations(message: Message):
    await cmd_liquidations(message)

@router.message(F.text == "📊 Доминация")
async def button_dominance(message: Message):
    await cmd_dominance(message)

@router.message(F.text == "🔔 Подписки")
async def button_subscribe(message: Message):
    await cmd_subscribe(message)

# Обработчик inline-кнопки "Назад"
@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.delete()  # удаляем сообщение с inline-клавиатурой
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_keyboard()
    )
    await callback.answer()

# Остальные команды (btc, whales, и т.д.) оставляем без изменений
# (они уже были в предыдущей версии, но нужно убедиться, что они не конфликтуют с текстовыми кнопками)
# Команда /subscribe теперь будет вызываться и из кнопки, и из команды
@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if not user:
            user = User(telegram_id=message.from_user.id)
            session.add(user)
            await session.commit()
        await message.answer(
            "Управление подписками:",
            reply_markup=subscription_keyboard(user)
        )

# Обработчик inline-кнопок подписок (был ранее) - без изменений
@router.callback_query(F.data.startswith("sub_"))
async def process_subscription(callback: CallbackQuery):
    sub_type = callback.data.split("_")[1]
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
        if user:
            if sub_type == "whales":
                user.subscribed_whales = not user.subscribed_whales
            elif sub_type == "liquidations":
                user.subscribed_liquidations = not user.subscribed_liquidations
            elif sub_type == "triggered":
                user.subscribed_triggered = not user.subscribed_triggered
            await session.commit()
        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(reply_markup=subscription_keyboard(user))
    await callback.answer("Настройки сохранены")