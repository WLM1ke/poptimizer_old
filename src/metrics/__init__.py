"""Метрики дивидендов и доходностей"""
import settings
from metrics.portfolio import Portfolio, CASH, PORTFOLIO

if settings.RETURNS_METRICS == 'BaseReturnsMetrics':
    from metrics.returns_metrics_base import BaseReturnsMetrics as ReturnsMetrics
elif settings.RETURNS_METRICS == 'MLReturnsMetrics':
    from metrics.returns_metrics_ml import MLReturnsMetrics as ReturnsMetrics

if settings.DIVIDENDS_METRICS == 'BaseDividendsMetrics':
    from metrics.dividends_metrics_base import BaseDividendsMetrics as DividendsMetrics
elif settings.DIVIDENDS_METRICS == 'MLDividendsMetrics':
    from metrics.dividends_metrics_ml import MLDividendsMetrics as DividendsMetrics
del settings
