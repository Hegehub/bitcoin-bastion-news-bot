from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
from services.api_client import api_client
from services.price_history import price_history
from services.nlp_service import nlp
from services.entity_service import entity_service
from services.price_categories import PriceCategorizer
from services.correlation import CorrelationAnalyzer
from config import TRIGGER_PRICE_CHANGE_PERCENT, TRIGGER_TIMEFRAME_MINUTES
from database import async_session, News
from sqlalchemy import select

logger = logging.getLogger(__name__)

class TriggerDetector:
    def __init__(self):
        self.trigger_change = TRIGGER_PRICE_CHANGE_PERCENT
        self.timeframe = TRIGGER_TIMEFRAME_MINUTES
        self.categorizer = PriceCategorizer()
        self.price_thresholds = {}
        # Веса источников (можно вынести в БД)
        self.source_weights = {
            'coindesk': 1.2,
            'cointelegraph': 1.1,
            'bitcoinmagazine': 1.0,
            'twitter': 0.8,
            'default': 1.0
        }

    async def update_thresholds(self, days: int = 30):
        async with async_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = await session.execute(
                select(News.price_change).where(
                    News.published_at >= cutoff,
                    News.price_change.isnot(None)
                )
            )
            changes = [float(x) for x in result.scalars().all() if x is not None]
            self.price_thresholds = self.categorizer.get_thresholds(changes)

    def _get_source_weight(self, source: str) -> float:
        """Возвращает вес источника для скоринга."""
        source_lower = source.lower()
        for key, weight in self.source_weights.items():
            if key in source_lower:
                return weight
        return self.source_weights['default']

    def _calculate_impact_score(self, news_article: Dict, sentiment_score: float,
                                entities: List[str], price_change: float) -> float:
        """
        Вычисляет скоринг важности новости на основе:
        - тональности
        - веса источника
        - количества важных сущностей
        - наличия специальных ключевых слов
        - величины изменения цены
        """
        source_weight = self._get_source_weight(news_article.get('source', ''))
        entity_bonus = min(len(entities) * 0.1, 0.5)  # максимум +0.5

        # Бонус за ключевые слова
        title = news_article['title'].lower()
        keyword_bonus = 0.0
        keywords = ['etf', 'sec', 'halving', 'blackrock', 'fidelity', 'fed']
        for kw in keywords:
            if kw in title:
                keyword_bonus += 0.2

        # Нормализованное изменение цены (0-1)
        price_factor = min(abs(price_change) / 10.0, 1.0) if price_change else 0

        impact = (
            sentiment_score * 0.4 +
            source_weight * 0.2 +
            entity_bonus * 0.2 +
            keyword_bonus * 0.1 +
            price_factor * 0.1
        )
        return round(min(impact, 1.0), 3)

    async def check_if_triggered(self, news_article: Dict) -> Optional[Dict]:
        tickers = news_article.get('tickers', [])
        if not tickers:
            tickers = self._extract_tickers(news_article['title'])
        if not tickers:
            tickers = ['BTC']
        primary_ticker = tickers[0]

        try:
            news_time = datetime.fromisoformat(news_article['published_at'].replace('Z', '+00:00'))
        except:
            news_time = datetime.utcnow() - timedelta(hours=1)
        check_time = news_time + timedelta(minutes=self.timeframe)

        # Извлечение сущностей
        entities = entity_service.get_important_entities(news_article['title'])

        # Получение тональности
        sentiment_data = await api_client.get_ai_sentiment(asset=primary_ticker, text=news_article['title'])
        if not sentiment_data:
            sentiment_result = nlp.analyze(news_article['title'])[0]
            sentiment_label = sentiment_result['label']
            sentiment_score = sentiment_result['score']
        else:
            sentiment_label = sentiment_data.get('label', 'neutral').lower()
            sentiment_score = sentiment_data.get('score', 0.5)

        price_change = await price_history.get_price_change_percent(primary_ticker, news_time, check_time)
        if price_change is None:
            logger.warning(f"Failed to get price change for {primary_ticker}")
            return None

        # Вычисление impact score
        impact_score = self._calculate_impact_score(news_article, sentiment_score, entities, price_change)

        # Определение категории
        category = self.categorizer.get_category(price_change, self.price_thresholds)

        if abs(price_change) >= self.trigger_change:
            direction_match = (
                (price_change > 0 and sentiment_label in ['positive', 'bullish', 'extreme_bullish']) or
                (price_change < 0 and sentiment_label in ['negative', 'bearish', 'extreme_bearish'])
            )
            if direction_match:
                news_article['triggered'] = True
                news_article['price_change'] = price_change
                news_article['sentiment'] = {'label': sentiment_label, 'score': sentiment_score}
                news_article['category'] = category
                news_article['impact_score'] = impact_score
                news_article['entities'] = entities
                logger.info(f"✅ Triggered news: {news_article['title'][:50]}... change: {price_change:+.2f}% impact: {impact_score}")
                return news_article
        return None

    def _extract_tickers(self, text: str) -> List[str]:
        common_tickers = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'LINK', 'MATIC', 'AVAX', 'UNI', 'ATOM', 'LTC', 'BCH', 'ALGO', 'XLM', 'VET', 'FIL', 'TRX', 'FTM', 'NEAR', 'APT', 'ARB', 'OP', 'SUI']
        words = text.upper().split()
        found = []
        for word in words:
            clean = word.strip('.,!?:;()[]{}"\'')
            if clean in common_tickers:
                found.append(clean)
        return found

    async def analyze_historical_news(self, days: int = 7) -> Dict:
        stats = {'total_analyzed': 0, 'triggered': 0, 'by_coin': {}, 'accuracy': 0}
        async with async_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = await session.execute(
                select(News).where(News.published_at >= cutoff)
            )
            news_list = result.scalars().all()
        for news in news_list:
            stats['total_analyzed'] += 1
            if news.triggered:
                stats['triggered'] += 1
                ticker = news.tickers.split(',')[0] if news.tickers else 'BTC'
                stats['by_coin'][ticker] = stats['by_coin'].get(ticker, 0) + 1
        if stats['total_analyzed'] > 0:
            stats['accuracy'] = (stats['triggered'] / stats['total_analyzed']) * 100
        return stats

trigger_detector = TriggerDetector()