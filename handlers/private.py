from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from services.api_client import api_client
from redis_cache import get_cache, set_cache
from database import add_user, async_session, User, select
from keyboards import main_keyboard, subscription_keyboard
import logging
import asyncio

router = Router()
logger = logging.getLogger(__name__)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
async def fetch_btc_price() -> str:
    """Получить цену BTC (используется в разных местах)"""
    metrics = await api_client.get_market_metrics()
    if not metrics or not metrics.get('btc_price'):
        return "Не удалось получить цену BTC"
    return f"💰 BTC: ${metrics['btc_price']:,.2f}"

# ========== ОСНОВНЫЕ КОМАНДЫ (ОПРЕДЕЛЯЕМ ДО КНОПОК) ==========

@router.message(Command("latest"))
async def cmd_latest(message: Message):
    """Последние новости"""
    news = await api_client.get_latest_news(limit=5)
    if not news:
        await message.answer("Новостей пока нет.")
        return
    text = "📰 **Последние новости:**\n\n"
    for item in news:
        text += f"• [{item['title']}]({item['url']}) — {item['source']}\n"
    await message.answer(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@router.message(Command("btc"))
async def cmd_btc(message: Message):
    """Цена BTC и метрики"""
    cached = await get_cache("market_metrics")
    if cached:
        await message.answer(cached, parse_mode=ParseMode.MARKDOWN)
        return

    metrics = await api_client.get_market_metrics()
    if not metrics or not metrics.get('btc_price'):
        await message.answer("Не удалось получить данные о рынке. Попробуйте позже.")
        return

    text = (
        f"💰 **Bitcoin (BTC)**\n"
        f"Цена: ${metrics['btc_price']:,.2f}\n\n"
        f"😨 Индекс страха и жадности: **{metrics['fear_greed']}**\n"
        f"({metrics['fear_greed_class']})\n"
        f"📊 Доминация BTC: {metrics['btc_dominance']:.2f}%\n"
        f"📊 Доминация ETH: {metrics['eth_dominance']:.2f}%"
    )
    await set_cache("market_metrics", text, ttl=300)
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("feargreed"))
async def cmd_feargreed(message: Message):
    """Индекс страха и жадности"""
    cached = await get_cache("fear_greed")
    if cached:
        await message.answer(cached)
        return
    fg = await api_client._make_request("/api/market/fear-greed")
    if not fg:
        await message.answer("Не удалось получить индекс.")
        return
    text = f"😨 Индекс страха и жадности: **{fg['value']}** — {fg['classification']}"
    await set_cache("fear_greed", text, ttl=600)
    await message.answer(text)

@router.message(Command("whales"))
async def cmd_whales(message: Message):
    """Китовые транзакции"""
    whales = await api_client.get_whale_transactions(limit=3)
    if not whales:
        await message.answer("Не удалось получить данные о китовых транзакциях.")
        return

    text = "🐋 **Последние китовые транзакции:**\n\n"
    for tx in whales:
        text += (
            f"• {tx['amount']:.2f} {tx['coin']} (${tx['value_usd']:,.0f})\n"
            f"  From: {tx['from'][:6]}... → To: {tx['to'][:6]}...\n"
            f"  [Смотреть]({tx['tx_url']})\n\n"
        )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@router.message(Command("liquidations"))
async def cmd_liquidations(message: Message):
    """Ликвидации"""
    liqs = await api_client.get_liquidations(limit=5)
    if not liqs:
        await message.answer("Не удалось получить данные о ликвидациях.")
        return

    text = "💥 **Последние ликвидации:**\n\n"
    for liq in liqs:
        emoji = "🟢" if liq['side'] == 'long' else "🔴"
        text += f"{emoji} {liq['side'].upper()} {liq['amount_usd']:,.0f}$ на {liq['pair']}\n"
    await message.answer(text)

@router.message(Command("dominance"))
async def cmd_dominance(message: Message):
    """Доминация"""
    cached = await get_cache("dominance")
    if cached:
        await message.answer(cached)
        return
    dom = await api_client._make_request("/api/dominance")
    if not dom:
        await message.answer("Не удалось получить доминацию.")
        return
    text = f"📊 Доминация BTC: {dom['btc_dominance']:.2f}%\n📊 Доминация ETH: {dom['eth_dominance']:.2f}%"
    await set_cache("dominance", text, ttl=600)
    await message.answer(text)

@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    """Управление подписками"""
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

# ========== СТАРТ И КНОПКИ ==========

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Приветствие и главная клавиатура"""
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    text = (
        "👋 Привет! Я бот крипто-аналитики.\n\n"
        "Я получаю новости в реальном времени и определяю, какие из них вызвали движение цены. "
        "Такие новости публикуются в канале.\n\n"
        "Используйте кнопки ниже для быстрого доступа к функциям."
    )
    await message.answer(text, reply_markup=main_keyboard())

# ========== ОБРАБОТЧИКИ ТЕКСТОВЫХ КНОПОК (ВЫЗЫВАЮТ КОМАНДЫ) ==========

@router.message(F.text == "📰 Последние новости")
async def button_latest(message: Message):
    await cmd_latest(message)

@router.message(F.text == "💰 Цена BTC")
async def button_btc(message: Message):
    await cmd_btc(message)

@router.message(F.text == "😨 Индекс страха")
async def button_feargreed(message: Message):
    await cmd_feargreed(message)  # теперь функция определена выше

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

# ========== ОБРАБОТЧИКИ INLINE-КНОПОК ==========

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("sub_"))
async def process_subscription(callback: CallbackQuery):
    """Обработка подписок"""
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
        await callback.message.edit_reply_markup(reply_markup=subscription_keyboard(user))
    await callback.answer("Настройки сохранены")