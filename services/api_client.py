import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from config import API_BASE_URL
import logging

logger = logging.getLogger(__name__)

class CryptoNewsAPIClient:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Универсальный метод для GET запросов к API."""
        url = f"{self.base_url}{endpoint}"
        try:
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed: {url} - Status: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Exception during API request to {url}: {e}")
            return None

    async def get_latest_news(self, limit: int = 20, language: str = 'en') -> Optional[List[Dict]]:
        """Получение последних новостей. /api/news"""
        data = await self._make_request("/api/news", params={"limit": limit, "language": language})
        return data.get("articles") if data else None

    async def get_news_by_ticker(self, ticker: str = "BTC", limit: int = 50) -> Optional[List[Dict]]:
        """Новости по конкретной монете из архива. /api/archive"""
        data = await self._make_request("/api/archive", params={"ticker": ticker, "limit": limit})
        return data.get("articles") if data else None

    async def get_ai_sentiment(self, asset: str = "BTC", text: Optional[str] = None) -> Optional[Dict]:
        """Получение тональности для актива или текста. /api/ai/sentiment"""
        params = {"asset": asset}
        if text:
            params["text"] = text
        return await self._make_request("/api/ai/sentiment", params=params)

    async def get_market_metrics(self) -> Dict[str, Any]:
        """Собрать все рыночные метрики в одном месте."""
        fg = await self._make_request("/api/market/fear-greed")
        btc_data = await self._make_request("/api/coin/bitcoin") # или /api/markets?ids=bitcoin
        dominance = await self._make_request("/api/dominance")
        
        # Парсим цену BTC из ответа coin/bitcoin
        btc_price = None
        if btc_data and 'market_data' in btc_data:
            btc_price = btc_data['market_data']['current_price']['usd']

        return {
            "btc_price": btc_price,
            "fear_greed": fg.get("value") if fg else None,
            "fear_greed_class": fg.get("classification") if fg else None,
            "btc_dominance": dominance.get("btc_dominance") if dominance else None,
            "eth_dominance": dominance.get("eth_dominance") if dominance else None,
        }

    async def get_whale_transactions(self, limit: int = 5) -> Optional[List[Dict]]:
        """Китовые транзакции. /api/whales"""
        data = await self._make_request("/api/whales", params={"limit": limit})
        return data.get("transactions") if data else None

    async def get_liquidations(self, limit: int = 5) -> Optional[List[Dict]]:
        """Ликвидации. /api/liquidations"""
        data = await self._make_request("/api/liquidations", params={"limit": limit})
        return data.get("liquidations") if data else None

    async def get_funding_rates(self) -> Optional[List[Dict]]:
        """Фандинг рейты. /api/funding"""
        data = await self._make_request("/api/funding")
        return data.get("rates") if data else None

    async def stream_news(self):
        """Генератор для получения событий из SSE-потока. /api/stream"""
        url = f"{self.base_url}/api/stream"
        try:
            session = await self._get_session()
            async with session.get(url, headers={'Accept': 'text/event-stream'}) as response:
                async for line in response.content:
                    if line:
                        # Парсинг SSE (упрощенно)
                        line = line.decode('utf-8').strip()
                        if line.startswith('data:'):
                            yield line[5:].strip()
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            return

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
