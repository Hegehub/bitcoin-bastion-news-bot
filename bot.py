import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from scheduler import start_scheduler
from middlewares import AdminCheckMiddleware
from handlers import private, group, channel, admin

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Подключаем middleware
dp.message.middleware(AdminCheckMiddleware())

# Регистрируем роутеры
dp.include_router(private.router)
dp.include_router(group.router)
dp.include_router(channel.router)
dp.include_router(admin.router)

async def main():
    await init_db()
    start_scheduler()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
