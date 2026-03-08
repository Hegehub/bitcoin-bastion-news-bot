from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

# Импортируем функции-задачи из соответствующих модулей
# Предположим, они находятся в пакете services
from services.news_checker import check_new_news          # проверка новостей
from services.trigger_detector import check_triggers      # анализ триггеров
from services.price_updater import update_prices          # обновление цен

logger = logging.getLogger(__name__)

# Создаём глобальный экземпляр планировщика (он будет доступен в bot.py при необходимости)
scheduler = AsyncIOScheduler()

def setup_schedulers(bot):
    """
    Настраивает и запускает все периодические задачи.
    Принимает экземпляр бота, который передаётся в задачи, где требуется отправка сообщений.
    """
    # Задача 1: проверка новых новостей каждую минуту
    scheduler.add_job(
        check_new_news,
        trigger=IntervalTrigger(minutes=1),
        args=[bot],          # передаём bot в функцию
        id="check_news",
        replace_existing=True
    )

    # Задача 2: анализ триггерных новостей каждые 5 минут
    scheduler.add_job(
        check_triggers,
        trigger=IntervalTrigger(minutes=5),
        args=[bot],
        id="check_triggers",
        replace_existing=True
    )

    # Задача 3: обновление кэша цен каждые 10 минут (не требует bot, поэтому без аргументов)
    scheduler.add_job(
        update_prices,
        trigger=IntervalTrigger(minutes=10),
        id="update_prices",
        replace_existing=True
    )

    # Запускаем планировщик
    scheduler.start()
    logger.info("✅ Планировщики успешно запущены")