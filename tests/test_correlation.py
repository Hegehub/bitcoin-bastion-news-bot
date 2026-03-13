import pytest
from services.correlation import CorrelationAnalyzer

def test_pearson_perfect():
    x = [1, 2, 3, 4]
    y = [2, 4, 6, 8]
    result = CorrelationAnalyzer.pearson(x, y)
    assert abs(result['corr'] - 1.0) < 1e-6
    assert result['p_value'] < 0.05

def test_cross_correlation():
    sentiment = [0, 1, 0, 1, 0]
    price = [10, 11, 10, 11, 10]
    result = CorrelationAnalyzer.cross_correlation(sentiment, price, max_lag=2)
    assert 1 in result
    assert abs(result[1] - 1.0) < 1e-6
