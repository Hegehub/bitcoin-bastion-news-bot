from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
from services.api_client import api_client
from services.trigger_detector import trigger_detector
from database import async_session, News, add_news_to_db, select
from handlers.group import publish_all_news_to_group
from config import CHANNEL_ID, GROUP_CHAT_ID
import asyncio

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def scheduled_news_check():
    """Периодическая проверка новых новостей на триггерность."""
    logger.info("Запуск проверки новых новостей...")
    news_list = await api_client.get_latest_news(limit=20)
    if not news_list:
        return

    for news in news_list:
        async with async_session() as session:
            exists = await session.execute(select(News).where(News.url == news['url']))
            if exists.scalar_one_or_none():
                continue

        db_news = await add_news_to_db(news)
        triggered_news = await trigger_detector.check_if_triggered(news)
        if triggered_news and db_news:
            async with async_session() as session:
                db_news.triggered = True
                db_news.price_change = triggered_news['price_change']
                db_news.sentiment_score = triggered_news['sentiment'].get('score')
                await session.commit()

            await publish_triggered_news_to_channel(triggered_news)

async def publish_triggered_news_to_channel(news_data):
    """Публикация триггерной новости в канал."""
    from bot import bot
    if not CHANNEL_ID:
        return
    price_change = news_data['price_change']
    direction = "📈" if price_change > 0 else "📉"
    sentiment = news_data['sentiment']['label']
    text = (
        f"{direction} **{news_data['title']}**\n\n"
        f"💰 Изменение цены: **{price_change:+.2f}%**\n"
        f"🧠 Тональность: **{sentiment}**\n"
        f"📅 {news_data['published_at']}\n\n"
        f"[Читать полностью]({news_data['url']})"
    )
    try:
        await bot.send_message(CHANNEL_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Не удалось отправить в канал: {e}")

def setup_schedulers(bot_instance):
    global bot
    bot = bot_instance
    scheduler.add_job(
        scheduled_news_check,
        trigger=IntervalTrigger(minutes=15),
        id="check_triggers",
        replace_existing=True
    )
    if GROUP_CHAT_ID:
        scheduler.add_job(
            publish_all_news_to_group,
            trigger=IntervalTrigger(minutes=60),
            args=[bot_instance],
            id="group_news_feed",
            replace_existing=True
        )
    scheduler.add_job(
        cleanup_old_cache,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_cache_cleanup",
        replace_existing=True
    )

async def cleanup_old_cache():
    from redis_cache import redis_client
    # Можно добавить логику очистки
    pass