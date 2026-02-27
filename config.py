import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")          # канал для публикаций
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# API
BIBABOT_API = "https://cryptocurrency.cv/api"
COINDESK_API = "https://api.coindesk.com/v1"  # уточнить
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"

# База данных
DATABASE_URL = "sqlite+aiosqlite:///crypto_bot.db"  # или PostgreSQL

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Планировщик
NEWS_CHECK_INTERVAL = 15  # минут
PRICE_UPDATE_INTERVAL = 5  # минут
