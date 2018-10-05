"""Реализация основных метрик дивидендного потока с помощью ML-модели"""
import pandas as pd

import ml.dividends.manager
from metrics.dividends_metrics import AbstractDividendsMetrics
from metrics.portfolio import Portfolio


class MLDividendsMetrics(AbstractDividendsMetrics):
    """Реализует основные метрики дивидендного потока для портфеля с помощью ML-модели

    ML-модели строится с помощью Gradient Boosting по данным с лагом о предыдущей дивидендной доходности и
    категориальной переменной на основе тикеров. СКО прогноза вычисляется с помощью кросс-валидации
    """

    @property
    def _tickers_real_after_tax_mean(self):
        portfolio = self._portfolio
        manager = ml.dividends.manager.DividendsMLDataManager(portfolio.positions[:-2],
                                                              pd.Timestamp(portfolio.date))
        return manager.value.prediction_mean

    @property
    def _tickers_real_after_tax_std(self):
        portfolio = self._portfolio
        manager = ml.dividends.manager.DividendsMLDataManager(portfolio.positions[:-2],
                                                              pd.Timestamp(portfolio.date))
        return manager.value.prediction_std


if __name__ == '__main__':
    from trading import POSITIONS, DATE, CASH

    port = Portfolio(date=DATE,
                     cash=CASH,
                     positions=POSITIONS)
    metrics = MLDividendsMetrics(port)
    print(metrics)
