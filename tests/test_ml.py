import pytest
from services.ml_trainer import ml_trainer
import pandas as pd

def test_model_training():
    # Создаём синтетические данные
    df = pd.DataFrame({
        'sentiment_score': [0.2, 0.8, 0.3, 0.9, 0.1, 0.7],
        'source_weight': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        'hour': [10, 14, 9, 15, 11, 13],
        'day_of_week': [1, 2, 1, 3, 4, 2],
        'has_etf': [0, 1, 0, 1, 0, 1],
        'has_sec': [0, 1, 0, 0, 0, 1],
        'has_halving': [0, 0, 0, 0, 0, 0],
        'entity_count': [1, 3, 2, 4, 1, 5],
        'target': [0, 1, 0, 1, 0, 1]
    })
    ml_trainer.train(df)
    assert ml_trainer.model is not None
    # Проверка предсказания
    features = {
        'sentiment_score': 0.9,
        'source_weight': 1.0,
        'hour': 14,
        'day_of_week': 2,
        'has_etf': 1,
        'has_sec': 1,
        'has_halving': 0,
        'entity_count': 4
    }
    proba = ml_trainer.predict_proba(features)
    assert 0 <= proba <= 1