from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from services.api_client import api_client
from redis_cache import get_cache, set_cache
from database import add_user, async_session, User, select
from keyboards import main_keyboard, subscription_keyboard
from config import ADMIN_IDS
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    # Проверяем, является ли пользователь админом
    is_admin_user = message.from_user.id in ADMIN_IDS or (user and user.is_admin)
    
    text = (
        "👋 **Привет! Я бот крипто-аналитики**\n\n"
        "📡 **Что я умею:**\n"
        "• Получаю новости о криптовалютах в реальном времени\n"
        "• Анализирую их тональность с помощью AI\n"
        "• Определяю, какие новости вызвали движение цены\n"
        "• Публикую важные новости в канале\n\n"
        "📊 **Доступные команды:**\n"
        "• `/btc` — цена BTC, страх/жадность, доминация\n"
        "• `/whales` — последние китовые транзакции\n"
        "• `/liquidations` — последние ликвидации\n"
        "• `/funding` — ставки фандинга\n"
        "• `/latest` — последние 5 новостей\n"
        "• `/feargreed` — индекс страха и жадности\n"
        "• `/dominance` — доминация BTC и ETH\n"
        "• `/subscribe` — управление подписками\n\n"
        "🔽 **Используйте кнопки ниже для быстрого доступа**"
    )
    
    if is_admin_user:
        text += "\n\n⚙️ **Вам доступна админ-панель** (кнопка внизу или команда /admin)"
    
    await message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard(is_admin_user))

# ========== ОБРАБОТЧИКИ ТЕКСТОВЫХ КНОПОК ==========

@router.message(F.text == "📰 Последние новости")
async def button_latest(message: Message):
    """Обработчик кнопки последних новостей"""
    await cmd_latest(message)

@router.message(F.text == "💰 Цена BTC")
async def button_btc(message: Message):
    """Обработчик кнопки цены BTC"""
    await cmd_btc(message)

@router.message(F.text == "😨 Индекс страха")
async def button_feargreed(message: Message):
    """Обработчик кнопки индекса страха"""
    await cmd_feargreed(message)

@router.message(F.text == "🐋 Киты")
async def button_whales(message: Message):
    """Обработчик кнопки китовых транзакций"""
    await cmd_whales(message)

@router.message(F.text == "💥 Ликвидации")
async def button_liquidations(message: Message):
    """Обработчик кнопки ликвидаций"""
    await cmd_liquidations(message)

@router.message(F.text == "📊 Доминация")
async def button_dominance(message: Message):
    """Обработчик кнопки доминации"""
    await cmd_dominance(message)

@router.message(F.text == "🔔 Подписки")
async def button_subscribe(message: Message):
    """Обработчик кнопки подписок"""
    await cmd_subscribe(message)

@router.message(F.text == "⚙️ Админ панель")
async def button_admin_panel(message: Message):
    """Обработчик кнопки админ-панели"""
    # Проверяем, действительно ли пользователь админ
    is_admin = message.from_user.id in ADMIN_IDS
    if not is_admin:
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
            is_admin = user.is_admin if user else False
    
    if is_admin:
        from handlers.admin import cmd_admin
        await cmd_admin(message)
    else:
        await message.answer("⛔ Доступ запрещен.")

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@router.message(Command("btc"))
async def cmd_btc(message: Message):
    """Показывает цену BTC, страх и жадность, доминацию"""
    # Пытаемся получить из кэша
    cached = await get_cache("market_metrics")
    if cached:
        await message.answer(cached, parse_mode=ParseMode.MARKDOWN)
        return

    # Отправляем сообщение о загрузке
    loading_msg = await message.answer("🔄 Загружаю данные о рынке...")

    # Получаем свежие данные
    metrics = await api_client.get_market_metrics()
    
    if not metrics or not metrics.get('btc_price'):
        await loading_msg.edit_text("❌ Не удалось получить данные о рынке. Попробуйте позже.")
        return

    # Формируем красивое сообщение
    text = (
        "💰 **Bitcoin (BTC)**\n"
        f"└ Цена: **${metrics['btc_price']:,.2f}**\n\n"
        
        "😨 **Индекс страха и жадности**\n"
        f"└ Значение: **{metrics['fear_greed']}** — {metrics['fear_greed_class']}\n\n"
        
        "📊 **Доминация**\n"
        f"└ BTC: **{metrics['btc_dominance']:.2f}%**\n"
        f"└ ETH: **{metrics['eth_dominance']:.2f}%**\n\n"
        
        "🔄 Обновлено: сейчас"
    )
    
    # Сохраняем в кэш на 5 минут
    await set_cache("market_metrics", text, ttl=300)
    
    # Удаляем сообщение о загрузке и отправляем результат
    await loading_msg.delete()
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("whales"))
async def cmd_whales(message: Message):
    """Показывает последние китовые транзакции"""
    loading_msg = await message.answer("🐋 Ищу крупные транзакции...")
    
    whales = await api_client.get_whale_transactions(limit=5)
    
    if not whales:
        await loading_msg.edit_text("❌ Не удалось получить данные о китовых транзакциях.")
        return

    text = "🐋 **Последние китовые транзакции:**\n\n"
    for i, tx in enumerate(whales, 1):
        # Определяем эмодзи в зависимости от монеты
        coin_emoji = "🟡" if tx.get('coin') == 'BTC' else "💎" if tx.get('coin') == 'ETH' else "🪙"
        
        text += (
            f"{i}. {coin_emoji} **{tx['amount']:.2f} {tx['coin']}**\n"
            f"   💵 Стоимость: **${tx['value_usd']:,.0f}**\n"
            f"   📤 От: `{tx['from'][:6]}...{tx['from'][-4:]}`\n"
            f"   📥 К: `{tx['to'][:6]}...{tx['to'][-4:]}`\n"
            f"   🔗 [Смотреть в блокчейне]({tx['tx_url']})\n\n"
        )
    
    await loading_msg.edit_text(
        text, 
        parse_mode=ParseMode.MARKDOWN, 
        disable_web_page_preview=True
    )

@router.message(Command("liquidations"))
async def cmd_liquidations(message: Message):
    """Показывает последние ликвидации"""
    loading_msg = await message.answer("💥 Загружаю данные о ликвидациях...")
    
    liqs = await api_client.get_liquidations(limit=5)
    
    if not liqs:
        await loading_msg.edit_text("❌ Не удалось получить данные о ликвидациях.")
        return

    text = "💥 **Последние ликвидации:**\n\n"
    for liq in liqs:
        emoji = "🟢" if liq.get('side') == 'long' else "🔴"
        side_text = "🟢 LONG" if liq.get('side') == 'long' else "🔴 SHORT"
        
        text += (
            f"{emoji} **{side_text}**\n"
            f"   💵 Сумма: **${liq['amount_usd']:,.0f}**\n"
            f"   📊 Пара: `{liq['pair']}`\n"
            f"   💰 Цена: **${liq['price']:,.2f}**\n\n"
        )
    
    await loading_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("funding"))
async def cmd_funding(message: Message):
    """Показывает ставки фандинга"""
    loading_msg = await message.answer("💰 Загружаю ставки фандинга...")
    
    rates = await api_client.get_funding_rates()
    
    if not rates:
        await loading_msg.edit_text("❌ Не удалось получить фандинг рейты.")
        return

    text = "💰 **Funding Rates (8h):**\n\n"
    for rate in rates[:10]:
        # Определяем цвет в зависимости от ставки
        if rate['rate'] > 0.01:
            emoji = "🟢🟢"
        elif rate['rate'] > 0:
            emoji = "🟢"
        elif rate['rate'] > -0.01:
            emoji = "🔴"
        else:
            emoji = "🔴🔴"
            
        text += f"{emoji} `{rate['pair']:8}`: **{rate['rate']*100:+.4f}%**\n"
    
    text += "\n_Положительные ставки — бычий настрой_"
    
    await loading_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("latest"))
async def cmd_latest(message: Message):
    """Показывает последние 5 новостей"""
    loading_msg = await message.answer("📰 Загружаю последние новости...")
    
    news = await api_client.get_latest_news(limit=5)
    
    if not news:
        await loading_msg.edit_text("❌ Не удалось получить новости.")
        return
        
    text = "📰 **Последние новости:**\n\n"
    for i, item in enumerate(news, 1):
        # Обрезаем слишком длинные заголовки
        title = item['title']
        if len(title) > 100:
            title = title[:97] + "..."
            
        text += f"{i}. [{title}]({item['url']})\n   └ {item['source']}\n\n"
    
    await loading_msg.edit_text(
        text, 
        parse_mode=ParseMode.MARKDOWN, 
        disable_web_page_preview=True
    )

@router.message(Command("feargreed"))
async def cmd_feargreed(message: Message):
    """Показывает индекс страха и жадности"""
    # Проверяем кэш
    cached = await get_cache("fear_greed")
    if cached:
        await message.answer(cached, parse_mode=ParseMode.MARKDOWN)
        return
    
    loading_msg = await message.answer("😨 Загружаю индекс страха и жадности...")
    
    fg = await api_client._make_request("/api/market/fear-greed")
    
    if not fg:
        await loading_msg.edit_text("❌ Не удалось получить индекс.")
        return
    
    # Определяем эмодзи в зависимости от значения
    value = fg['value']
    if value <= 25:
        emoji = "😱"
        status = "Экстремальный страх"
    elif value <= 45:
        emoji = "😨"
        status = "Страх"
    elif value <= 55:
        emoji = "😐"
        status = "Нейтрально"
    elif value <= 75:
        emoji = "😊"
        status = "Жадность"
    else:
        emoji = "🤑"
        status = "Экстремальная жадность"
    
    text = (
        f"{emoji} **Индекс страха и жадности**\n\n"
        f"Значение: **{value}** — {fg['classification']}\n"
        f"Статус: **{status}**\n\n"
        f"📊 _Индекс показывает настроение рынка_\n"
        f"0-25: страх, 75-100: жадность"
    )
    
    # Сохраняем в кэш на 10 минут
    await set_cache("fear_greed", text, ttl=600)
    
    await loading_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("dominance"))
async def cmd_dominance(message: Message):
    """Показывает доминацию BTC и ETH"""
    # Проверяем кэш
    cached = await get_cache("dominance")
    if cached:
        await message.answer(cached, parse_mode=ParseMode.MARKDOWN)
        return
    
    loading_msg = await message.answer("📊 Загружаю данные о доминации...")
    
    dom = await api_client._make_request("/api/dominance")
    
    if not dom:
        await loading_msg.edit_text("❌ Не удалось получить доминацию.")
        return
    
    # Определяем тренд (если есть данные за предыдущий период)
    btc_trend = "↗️" if dom.get('btc_dominance_change_24h', 0) > 0 else "↘️"
    eth_trend = "↗️" if dom.get('eth_dominance_change_24h', 0) > 0 else "↘️"
    
    text = (
        "📊 **Доминация на рынке**\n\n"
        f"🟠 **Bitcoin** {btc_trend}\n"
        f"└ {dom['btc_dominance']:.2f}%\n\n"
        f"🔵 **Ethereum** {eth_trend}\n"
        f"└ {dom['eth_dominance']:.2f}%\n\n"
        f"📈 Остальные альткоины: **{(100 - dom['btc_dominance'] - dom['eth_dominance']):.2f}%**"
    )
    
    # Сохраняем в кэш на 10 минут
    await set_cache("dominance", text, ttl=600)
    
    await loading_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    """Управление подписками"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if not user:
            user = User(telegram_id=message.from_user.id)
            session.add(user)
            await session.commit()
        
        text = (
            "🔔 **Управление подписками**\n\n"
            "Вы можете подписаться на уведомления о:\n"
            "• 🐋 Китовых транзакциях\n"
            "• 💥 Ликвидациях\n"
            "• 📰 Триггерных новостях\n\n"
            "Уведомления будут приходить в личные сообщения."
        )
        
        await message.answer(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscription_keyboard(user)
        )

# ========== ОБРАБОТЧИКИ INLINE КНОПОК ==========

@router.callback_query(F.data.startswith("sub_"))
async def process_subscription(callback: CallbackQuery):
    """Обработка нажатий на кнопки подписок"""
    sub_type = callback.data.split("_")[1]
    
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
        
        if user:
            if sub_type == "whales":
                user.subscribed_whales = not user.subscribed_whales
                status = "включены" if user.subscribed_whales else "отключены"
                await callback.answer(f"Уведомления о китах {status}")
                
            elif sub_type == "liquidations":
                user.subscribed_liquidations = not user.subscribed_liquidations
                status = "включены" if user.subscribed_liquidations else "отключены"
                await callback.answer(f"Уведомления о ликвидациях {status}")
                
            elif sub_type == "triggered":
                user.subscribed_triggered = not user.subscribed_triggered
                status = "включены" if user.subscribed_triggered else "отключены"
                await callback.answer(f"Уведомления о триггерных новостях {status}")
            
            await session.commit()
            
            # Обновляем клавиатуру
            await callback.message.edit_reply_markup(
                reply_markup=subscription_keyboard(user)
            )
        else:
            await callback.answer("Ошибка: пользователь не найден", show_alert=True)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    # Проверяем, является ли пользователь админом для правильной клавиатуры
    is_admin = callback.from_user.id in ADMIN_IDS
    if not is_admin:
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
            is_admin = user.is_admin if user else False
    
    await callback.message.delete()
    await callback.message.answer(
        "🔽 Главное меню:",
        reply_markup=main_keyboard(is_admin)
    )
    await callback.answer()

# ========== ОБРАБОТЧИК ДЛЯ НЕИЗВЕСТНЫХ КОМАНД ==========

@router.message()
async def handle_unknown(message: Message):
    """Обработчик неизвестных сообщений"""
    if message.text and not message.text.startswith('/'):
        # Игнорируем обычный текст (кнопки уже обработаны выше)
        return
    
    await message.answer(
        "❓ Неизвестная команда.\n"
        "Используйте /start для просмотра доступных команд."
    )