import aioredis
import json
from config import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)

async def get_cached_price(asset="BTC"):
    data = await redis.get(f"price:{asset}")
    return json.loads(data) if data else None

async def set_cached_price(asset, price_data, ttl=300):  # 5 минут
    await redis.setex(f"price:{asset}", ttl, json.dumps(price_data))

# Аналогично для других метрик
