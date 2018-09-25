"""Реализация основных метрик дивидендного потока с помощью ML-модели"""
import pandas as pd

import ml.ml_dividends.manager
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
        manager = ml.ml_dividends.manager.DividendsMLDataManager(portfolio.positions[:-2],
                                                                 pd.Timestamp(portfolio.date))
        return manager.value.div_prediction

    @property
    def _tickers_real_after_tax_std(self):
        portfolio = self._portfolio
        manager = ml.ml_dividends.manager.DividendsMLDataManager(portfolio.positions[:-2],
                                                                 pd.Timestamp(portfolio.date))
        return pd.Series(manager.value.std, index=portfolio.positions[:-2])


if __name__ == '__main__':
    try:
        from trading import POSITIONS, DATE, CASH
    except ModuleNotFoundError:
        POSITIONS = ['AKRN']
        DATE = '2018-09-06'
    port = Portfolio(date=DATE,
                     cash=CASH,
                     positions=POSITIONS)
    print(MLDividendsMetrics(port))
