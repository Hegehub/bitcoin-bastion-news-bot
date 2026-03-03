import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from services.api_client import CryptoNewsAPIClient
import logging
from config import TRIGGER_PRICE_CHANGE_PERCENT, TRIGGER_TIMEFRAME_MINUTES

logger = logging.getLogger(__name__)

class TriggerDetector:
    def __init__(self, api_client: CryptoNewsAPIClient):
        self.api_client = api_client
        self.trigger_change = TRIGGER_PRICE_CHANGE_PERCENT
        self.timeframe = TRIGGER_TIMEFRAME_MINUTES

    async def check_if_triggered(self, news_article: Dict) -> Optional[Dict]:
        """
        Проверяет, вызвала ли новость движение цены.
        Возвращает обогащенную новость с данными о триггере или None.
        """
        tickers = news_article.get('tickers', ['BTC']) # Предположим, API возвращает тикеры
        if not tickers:
            tickers = ['BTC']

        # Берем первый тикер для простоты
        asset = tickers[0]
        news_time = datetime.fromisoformat(news_article['published_at'].replace('Z', '+00:00'))

        # Загружаем цену актива через API (нужен эндпоинт исторических цен, например /api/coin/history)
        # Упрощенно: будем использовать тональность и время, т.к. API может не иметь исторических цен
        # В реальности: запросить цену через /api/archive?ticker=BTC&date=... и сравнить.
        
        # Альтернативный подход через API тональности
        sentiment_data = await self.api_client.get_ai_sentiment(asset=asset, text=news_article['title'])
        if not sentiment_data:
            return None

        # Здесь должна быть логика с запросом цены через отдельный API (например, CoinGecko)
        # Пока используем заглушку - предполагаем, что новость с высоким sentiment - триггерная
        # В реальном проекте это будет полноценный запрос к историческому API цен.
        
        # Симуляция проверки изменения цены (заглушка)
        price_change = await self._simulate_price_change(asset, news_time)
        
        if price_change is not None and abs(price_change) >= self.trigger_change:
            # Проверяем, совпадает ли знак изменения с тональностью
            sentiment_label = sentiment_data.get('label', 'neutral')
            if (price_change > 0 and sentiment_label == 'positive') or \
               (price_change < 0 and sentiment_label == 'negative'):
                news_article['triggered'] = True
                news_article['price_change'] = price_change
                news_article['sentiment'] = sentiment_data
                return news_article
        return None

    async def _simulate_price_change(self, asset: str, since_time: datetime) -> Optional[float]:
        """ЗАГЛУШКА. В реальности - запрос к историческому API цен."""
        # Эта функция должна:
        # 1. Запросить цену на момент since_time
        # 2. Запросить цену через self.timeframe минут после since_time
        # 3. Рассчитать процентное изменение
        # 4. Вернуть его.
        # Пока возвращаем случайное число для демонстрации.
        import random
        return round(random.uniform(-3.0, 3.0), 2)
