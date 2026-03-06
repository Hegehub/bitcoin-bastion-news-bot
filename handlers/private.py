from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from services.api_client import api_client
from services.price_history import price_history
from services.cryptorank_client import cryptorank
from services.trigger_detector import trigger_detector
from redis_cache import get_cache, set_cache
from database import add_user, async_session, User, select
from keyboards import (
    main_menu_keyboard, subscription_keyboard, language_keyboard,
    ai_menu_keyboard, market_menu_keyboard, research_menu_keyboard,
    international_languages_keyboard, reaction_keyboard
)
from utils import escape_html
import logging
from fluent.runtime import FluentLocalization, FluentResourceLoader
import os
import json

router = Router()
logger = logging.getLogger(__name__)

loader = FluentResourceLoader("locales/{locale}")

async def get_user_language(user_id: int) -> str:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == user_id))
        if user and user.language:
            return user.language
    return 'en'

async def set_user_language(user_id: int, language: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == user_id))
        if user:
            user.language = language
        else:
            user = User(telegram_id=user_id, language=language)
            session.add(user)
        await session.commit()

def get_text(msg_id: str, lang: str = 'en', **kwargs) -> str:
    escaped_kwargs = {k: escape_html(v) if isinstance(v, str) else v for k, v in kwargs.items()}
    try:
        l10n = FluentLocalization([lang], ["messages.ftl"], loader)
        return l10n.format_value(msg_id, escaped_kwargs)
    except:
        l10n_en = FluentLocalization(['en'], ["messages.ftl"], loader)
        return l10n_en.format_value(msg_id, escaped_kwargs)

class AIStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_url = State()
    waiting_for_factcheck = State()
    waiting_for_entities = State()
    waiting_for_coin = State()
    waiting_for_historical_ticker = State()
    waiting_for_orderbook_pair = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.first_name)
    lang = await get_user_language(user_id)
    text = get_text("start_message", lang)
    await message.answer(text, reply_markup=main_menu_keyboard(lang))

@router.message(Command("language"))
async def cmd_language(message: Message):
    await message.answer("Choose language / Выберите язык:", reply_markup=language_keyboard())

@router.callback_query(F.data.startswith("lang_"))
async def process_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await set_user_language(callback.from_user.id, lang)
    text = get_text("language_selected", lang)
    await callback.message.edit_text(text)
    await callback.answer()

@router.message(Command("btc"))
async def cmd_btc(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    cached = await get_cache("global_metrics")
    if cached:
        await message.answer(cached, parse_mode=ParseMode.HTML)
        return

    metrics = await cryptorank.get_global_metrics()
    if not metrics:
        await message.answer(get_text("no_data", lang))
        return

    btc_price = metrics.get("btcPrice")
    fear_greed = metrics.get("fearGreed")
    btc_dominance = metrics.get("btcDominance")
    eth_dominance = metrics.get("ethDominance")

    if fear_greed is not None:
        if fear_greed < 20:
            fear_class = "Extreme Fear" if lang == 'en' else "Экстремальный страх"
        elif fear_greed < 40:
            fear_class = "Fear" if lang == 'en' else "Страх"
        elif fear_greed < 60:
            fear_class = "Neutral" if lang == 'en' else "Нейтрально"
        elif fear_greed < 80:
            fear_class = "Greed" if lang == 'en' else "Жадность"
        else:
            fear_class = "Extreme Greed" if lang == 'en' else "Экстремальная жадность"
    else:
        fear_class = "Unknown" if lang == 'en' else "Неизвестно"

    text = get_text("btc_price", lang,
                   price=btc_price,
                   fear=fear_greed,
                   fear_class=fear_class,
                   btc_dom=btc_dominance,
                   eth_dom=eth_dominance)
    
    await set_cache("global_metrics", text, ttl=300)
    await message.answer(text, parse_mode=ParseMode.HTML)

# Остальные команды (whales, liquidations, funding, latest, historical, international, ask, summarize, factcheck, entities, gainers, losers, coin, heatmap, options, orderbook, feargreed, dominance, subscribe) остаются без изменений (используют api_client).
# Для экономии места здесь не дублируются, но в реальном проекте они должны быть полными.

@router.message(Command("whales"))
async def cmd_whales(message: Message):
    # ... использует api_client.get_whale_transactions ...
    pass

# ... и так далее для всех команд ...

# Обработчики реакций
@router.callback_query(F.data.startswith("react_"))
async def process_reaction(callback: CallbackQuery):
    parts = callback.data.split("_")
    reaction = parts[1]
    news_id = int(parts[2])
    await callback.answer(f"Вы выбрали {reaction}!")

# Обработчики меню (аналогично предыдущим версиям)
@router.callback_query(F.data == "menu_main")
async def menu_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    await callback.message.edit_text(
        get_text("start_message", lang),
        reply_markup=main_menu_keyboard(lang)
    )
    await callback.answer()

# ... и так далее ...