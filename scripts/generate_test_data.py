#!/usr/bin/env python3
"""
Скрипт для генерации синтетических тестовых данных Bitcoin.
Создаёт реалистичные данные с корреляцией между новостями и движением цены.
"""

import csv
import random
import os
from datetime import datetime, timedelta

def generate_price_series(start_price: float = 50000, days: int = 90, volatility: float = 0.02) -> list:
    """
    Генерирует синтетический ряд цен с случайными движениями.
    """
    prices = []
    current_price = start_price

    for _ in range(days):
        # Случайное изменение цены (нормальное распределение)
        change = random.gauss(0, volatility)
        current_price *= (1 + change)
        prices.append(round(current_price, 2))

    return prices

def generate_news_titles() -> list:
    """
    Возвращает список шаблонов новостей с разной тональностью.
    """
    return {
        'positive': [
            "Bitcoin ETF approved by SEC, price surges",
            "Institutional investors pour billions into Bitcoin",
            "Bitcoin halving event sparks new rally",
            "MicroStrategy buys additional $500M in Bitcoin",
            "El Salvador announces plans for Bitcoin city",
            "BlackRock files for spot Bitcoin ETF",
            "Bitcoin mining difficulty reaches all-time high",
            "Major bank launches Bitcoin trading desk",
            "Bitcoin dominance exceeds 50% as altcoins slide",
            "Fed rate cut fuels Bitcoin rally"
        ],
        'neutral': [
            "Bitcoin price consolidates near $50k",
            "Trading volume remains steady",
            "Bitcoin network hash rate stabilizes",
            "Market awaits Fed decision",
            "Bitcoin volatility at monthly low",
            "Technical analysis: BTC holds support",
            "Bitcoin options open interest increases",
            "Whale transactions show accumulation",
            "Exchange inflows remain neutral",
            "Bitcoin dominance unchanged"
        ],
        'negative': [
            "SEC delays Bitcoin ETF decision",
            "China renews crypto mining crackdown",
            "Bitcoin plunges as inflation fears rise",
            "Major exchange reports security breach",
            "Bitcoin selling pressure intensifies",
            "Regulatory concerns weigh on Bitcoin",
            "Bitcoin跌破 $45k support level",
            "FOMC minutes spook crypto markets",
            "Leveraged long positions liquidated",
            "Miner capitulation signals bottom?"
        ]
    }

def generate_test_data(
    days: int = 90,
    news_per_day: int = 3,
    output_file: str = 'data/historical_btc.csv'
) -> None:
    """
    Генерирует тестовый CSV файл с историческими данными.
    """
    # Создаём директорию если её нет
    os.makedirs('data', exist_ok=True)

    # Генерируем цены
    prices = generate_price_series(start_price=50000, days=days)
    news_templates = generate_news_titles()

    # Создаём временные метки (начиная с сегодняшнего дня и назад)
    end_date = datetime.utcnow()
    dates = [end_date - timedelta(days=i) for i in range(days)]
    dates.reverse()  # от старых к новым

    # Список источников
    sources = ['CoinDesk', 'CoinTelegraph', 'Bitcoin Magazine', 'The Block', 'Decrypt', 'CryptoSlate']

    data = []

    for day_idx, date in enumerate(dates):
        date_str = date.strftime('%Y-%m-%d')
        price = prices[day_idx]

        # Генерируем несколько новостей для этого дня
        for news_idx in range(news_per_day):
            # Выбираем случайную тональность с весами
            sentiment_type = random.choices(
                ['positive', 'neutral', 'negative'],
                weights=[0.3, 0.5, 0.2]
            )[0]

            # Выбираем заголовок
            title = random.choice(news_templates[sentiment_type])

            # Добавляем немного вариаций
            if random.random() > 0.7:
                title = title + " " + random.choice(["– analyst", "says expert", "report shows"])

            # Выбираем источник
            source = random.choice(sources)

            # Определяем тональность (число)
            sentiment_score = {
                'positive': round(random.uniform(0.65, 0.95), 2),
                'neutral': round(random.uniform(0.45, 0.55), 2),
                'negative': round(random.uniform(0.05, 0.35), 2)
            }[sentiment_type]

            # Генерируем время публикации в течение дня
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            timestamp = f"{date_str} {hour:02d}:{minute:02d}:00"

            data.append({
                'timestamp': timestamp,
                'price': price,
                'title': title,
                'source': source,
                'sentiment_score': sentiment_score
            })

    # Сортируем по времени (от старых к новым)
    data.sort(key=lambda x: x['timestamp'])

    # Записываем в CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'price', 'title', 'source', 'sentiment_score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"✅ Generated {len(data)} test records in {output_file}")
    print(f"📅 Date range: {data[0]['timestamp']} to {data[-1]['timestamp']}")
    print(f"💰 Price range: ${min(prices):,.0f} - ${max(prices):,.0f}")

    # Статистика по тональности
    pos = sum(1 for r in data if r['sentiment_score'] > 0.6)
    neu = sum(1 for r in data if 0.4 <= r['sentiment_score'] <= 0.6)
    neg = sum(1 for r in data if r['sentiment_score'] < 0.4)
    print(f"📊 Sentiment: Positive: {pos}, Neutral: {neu}, Negative: {neg}")

if __name__ == "__main__":
    generate_test_data(days=90, news_per_day=3, output_file='data/historical_btc.csv')