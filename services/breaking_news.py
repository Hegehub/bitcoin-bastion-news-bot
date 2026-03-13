from datetime import datetime, timedelta
from typing import List, Dict, Optional
from redis_cache import get_cache, set_cache
import hashlib
import logging

logger = logging.getLogger(__name__)

class BreakingNewsDetector:
    def __init__(self, redis_client, window_minutes: int = 10, threshold: int = 3):
        self.redis = redis_client
        self.window = window_minutes * 60  # в секундах
        self.threshold = threshold
        self.prefix = "breaking:"

    def _get_key(self, title: str) -> str:
        """Создаёт хеш заголовка для группировки похожих новостей."""
        # Упрощённо: берём первые 50 символов и удаляем стоп-слова
        # В реальности лучше использовать семантическое сравнение
        simplified = ' '.join(title.lower().split()[:10])
        hash_obj = hashlib.md5(simplified.encode())
        return self.prefix + hash_obj.hexdigest()

    async def add_news(self, news_item: Dict) -> bool:
        """Добавляет новость в кэш и проверяет, является ли она breaking."""
        title = news_item.get('title', '')
        key = self._get_key(title)
        now = datetime.utcnow().timestamp()

        # Получаем текущий список временных меток для этого хеша
        timestamps = await get_cache(key) or []
        # Оставляем только те, что попадают в окно
        timestamps = [ts for ts in timestamps if ts > now - self.window]
        timestamps.append(now)
        await set_cache(key, timestamps, ttl=self.window)

        if len(timestamps) >= self.threshold:
            logger.info(f"Breaking news detected: {title[:50]}... ({len(timestamps)} sources)")
            return True
        return False

    async def get_breaking_news(self, title: str) -> Optional[Dict]:
        """Возвращает информацию о breaking-новости, если она есть."""
        key = self._get_key(title)
        timestamps = await get_cache(key) or []
        if len(timestamps) >= self.threshold:
            return {
                'title': title,
                'source_count': len(timestamps),
                'first_seen': datetime.fromtimestamp(min(timestamps)).isoformat()
            }
        return None

# Глобальный экземпляр будет инициализирован в scheduler.py