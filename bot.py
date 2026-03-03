import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from handlers import private, group, admin
from middlewares import AdminCheckMiddleware
from scheduler import setup_schedulers, scheduler
from services.api_client import CryptoNewsAPIClient
from database import init_db
import redis_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Регистрация роутеров
dp.include_router(private.router)
dp.include_router(group.router)
dp.include_router(admin.router)

# Middleware
dp.message.middleware(AdminCheckMiddleware())

async def on_startup():
    """Действия при запуске бота."""
    logger.info("Запуск бота...")
    await init_db()
    await redis_cache.init_redis()
    
    # Инициализируем клиент API (он создаст сессию)
    api_client = CryptoNewsAPIClient()
    await api_client._get_session()
    
    # Настраиваем и запускаем планировщик
    setup_schedulers()
    scheduler.start()
    logger.info("Планировщик запущен.")

async def on_shutdown():
    """Действия при остановке бота."""
    logger.info("Остановка бота...")
    scheduler.shutdown()
    await redis_cache.close_redis()
    # Закрываем сессию API клиента
    from services.api_client import api_client
    await api_client.close()
    await dp.storage.close()
    await bot.session.close()

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
