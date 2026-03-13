from celery import Celery
import os
import asyncio
from services.trigger_detector import trigger_detector
from database import async_session, add_news_to_db

app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@app.task
def process_news(news_item: dict):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_process(news_item))

async def _process(news_item):
    db_news = await add_news_to_db(news_item)
    triggered = await trigger_detector.check_if_triggered(news_item)
    if triggered and db_news:
        async with async_session() as session:
            db_news.triggered = True
            db_news.price_change = triggered['price_change']
            db_news.sentiment_score = triggered['sentiment'].get('score')
            await session.commit()
        # Здесь можно отправить уведомление в Telegram через бота
        # Для этого нужен доступ к bot instance, можно передавать через message broker
