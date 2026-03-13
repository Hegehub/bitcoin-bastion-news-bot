#!/usr/bin/env python3
"""
Скрипт для загрузки исторических данных Bitcoin через CryptoRank API
и сохранения в формате CSV для бэктестинга.
"""

import asyncio
import csv
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Добавляем путь к проекту для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.cryptorank_client import cryptorank
from services.api_client import api_client
from config import CRYPTORANK_API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoricalDataDownloader:
    def __init__(self):
        self.btc_id = 1  # ID Bitcoin в CryptoRank (обычно 1)

    async def get_btc_price_history(self, days: int = 90) -> List[Dict]:
        """
        Загружает историю цен Bitcoin за указанное количество дней.
        Использует эндпоинт /sparkline с интервалом 1 день.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Downloading BTC price history from {start_date} to {end_date}")

        # Получаем sparkline данные
        points = await cryptorank.get_sparkline(
            currency_id=self.btc_id,
            from_time=start_date,
            to_time=end_date,
            interval="1d"  # дневные данные
        )

        if not points:
            logger.error("Failed to get price history from CryptoRank")
            return []

        history = []
        for point in points:
            history.append({
                'timestamp': datetime.fromtimestamp(point['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                'price': point['price'],
                'volume': point.get('volume', 0)
            })

        logger.info(f"Downloaded {len(history)} price points")
        return history

    async def get_historical_news(self, days: int = 90, limit_per_day: int = 5) -> List[Dict]:
        """
        Загружает исторические новости из free-crypto-news API.
        """
        end_date = datetime.utcnow()
        news_list = []

        logger.info(f"Downloading historical news for last {days} days")

        # Загружаем новости порциями по дням
        for i in range(days):
            current_date = end_date - timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')

            # Пробуем получить новости за конкретную дату
            news = await api_client.get_historical_archive(
                date=date_str,
                ticker='BTC',
                limit=limit_per_day
            )

            if news:
                for item in news:
                    news_list.append({
                        'timestamp': item.get('published_at', date_str + ' 12:00:00'),
                        'price': 0,  # будет заполнено позже
                        'title': item.get('title', ''),
                        'source': item.get('source', 'unknown'),
                        'sentiment_score': 0.5  # будет рассчитано позже
                    })

            # Небольшая задержка чтобы не превысить rate limit
            await asyncio.sleep(0.5)

        logger.info(f"Downloaded {len(news_list)} news items")
        return news_list

    async def enrich_with_sentiment(self, news_list: List[Dict]) -> List[Dict]:
        """
        Обогащает новости тональностью через FinBERT.
        """
        from services.nlp_service import nlp

        logger.info("Calculating sentiment for news...")
        enriched = []

        for news in news_list:
            sentiment = nlp.analyze(news['title'])[0]
            # Преобразуем метку в числовое значение
            score_map = {'positive': 0.8, 'neutral': 0.5, 'negative': 0.2}
            sentiment_score = score_map.get(sentiment['label'], 0.5)

            news['sentiment_score'] = sentiment_score
            enriched.append(news)

            # Небольшая задержка для GPU
            await asyncio.sleep(0.1)

        return enriched

    def match_prices_to_news(self, news_list: List[Dict], price_history: List[Dict]) -> List[Dict]:
        """
        Сопоставляет новости с ближайшими по времени ценами.
        """
        # Создаём словарь цен по датам для быстрого доступа
        price_by_day = {}
        for price_point in price_history:
            day = price_point['timestamp'][:10]  # YYYY-MM-DD
            price_by_day[day] = price_point['price']

        result = []
        for news in news_list:
            news_day = news['timestamp'][:10]
            if news_day in price_by_day:
                news['price'] = price_by_day[news_day]
                result.append(news)

        logger.info(f"Matched {len(result)} news with price data")
        return result

    async def save_to_csv(self, data: List[Dict], filename: str = 'data/historical_btc.csv'):
        """
        Сохраняет данные в CSV файл.
        """
        os.makedirs('data', exist_ok=True)

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'price', 'title', 'source', 'sentiment_score']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for row in data:
                # Убеждаемся, что все поля есть
                writer.writerow({
                    'timestamp': row.get('timestamp', ''),
                    'price': row.get('price', 0),
                    'title': row.get('title', ''),
                    'source': row.get('source', 'unknown'),
                    'sentiment_score': row.get('sentiment_score', 0.5)
                })

        logger.info(f"Data saved to {filename}")

    async def run(self, days: int = 90):
        """
        Основной метод для загрузки и сохранения данных.
        """
        # 1. Загружаем историю цен
        price_history = await self.get_btc_price_history(days)
        if not price_history:
            logger.error("Failed to get price history")
            return

        # 2. Загружаем новости
        news_list = await self.get_historical_news(days)

        # 3. Рассчитываем тональность
        news_with_sentiment = await self.enrich_with_sentiment(news_list)

        # 4. Сопоставляем с ценами
        final_data = self.match_prices_to_news(news_with_sentiment, price_history)

        # 5. Сохраняем
        await self.save_to_csv(final_data)

        # Статистика
        logger.info(f"✅ Completed! Saved {len(final_data)} records")
        if final_data:
            positive = sum(1 for n in final_data if n['sentiment_score'] > 0.6)
            negative = sum(1 for n in final_data if n['sentiment_score'] < 0.4)
            logger.info(f"Sentiment distribution: Positive: {positive}, Neutral: {len(final_data)-positive-negative}, Negative: {negative}")

async def main():
    downloader = HistoricalDataDownloader()
    await downloader.run(days=90)  # Загружаем за последние 90 дней

if __name__ == "__main__":
    asyncio.run(main())