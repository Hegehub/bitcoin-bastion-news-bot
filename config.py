import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Для публикации триггерных новостей
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID") # ID группы для ленты всех новостей
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")

# Настройки для определения "триггерных" новостей
TRIGGER_PRICE_CHANGE_PERCENT = float(os.getenv("TRIGGER_PRICE_CHANGE_PERCENT", 1.5)) # Изменение цены в %
TRIGGER_TIMEFRAME_MINUTES = int(os.getenv("TRIGGER_TIMEFRAME_MINUTES", 30)) # За какой период проверять

# Базовый URL API
API_BASE_URL = "https://cryptocurrency.cv"
