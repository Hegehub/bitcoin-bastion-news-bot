import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, CHANNEL_ID
from database import init_db
from news_analyzer import NewsAnalyzer
from scheduler import start_scheduler
from middlewares import AdminCheckMiddleware
from handlers import private, group, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Middleware
dp.message.middleware(AdminCheckMiddleware())

# Роутеры
dp.include_router(private.router)
dp.include_router(group.router)
dp.include_router(admin.router)

analyzer = None

async def on_startup():
    global analyzer
    await init_db()
    # Запускаем анализатор со стримингом
    analyzer = NewsAnalyzer(bot)
    await analyzer.start_streaming()
    # Запускаем планировщик
    start_scheduler(bot, CHANNEL_ID)
    logger.info("Bot started")

async def on_shutdown():
    if analyzer:
        await analyzer.close()
    await bot.session.close()
    logger.info("Bot stopped")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
