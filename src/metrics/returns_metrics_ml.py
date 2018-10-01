"""Основные метрики доходности на базе ML-модели"""
import pandas as pd

from metrics.portfolio import CASH, PORTFOLIO, Portfolio
from metrics.returns_metrics import AbstractReturnsMetrics
from ml.returns import cases
from ml.returns.manager import ReturnsMLDataManager


class MLReturnsMetrics(AbstractReturnsMetrics):
    def __init__(self, portfolio: Portfolio):
        super().__init__(portfolio)
        manager = ReturnsMLDataManager(portfolio.positions[:-2], pd.Timestamp(portfolio.date))
        self._ml_data = manager.value

    @property
    def returns(self):
        """Доходности составляющих портфеля и самого портфеля"""
        portfolio = self._portfolio
        returns = cases.log_returns_with_div(portfolio.positions[:-2], pd.Timestamp(portfolio.date))
        returns = returns.reindex(columns=self._portfolio.positions)
        returns[CASH] = 0
        weight = self._portfolio.weight.iloc[:-2].transpose()
        returns[PORTFOLIO] = returns.iloc[:, :-2].multiply(weight).sum(axis=1)
        return returns

    @property
    def decay(self):
        """Константа сглаживания"""
        return 1 - 1 / self._ml_data.params['data']['ew_lags']

    @property
    def mean(self):
        """Series матожидания доходности"""
        mean = self._ml_data.prediction_mean
        mean[CASH] = 0
        weighted_mean = mean * self._portfolio.weight[mean.index]
        mean[PORTFOLIO] = weighted_mean.sum(axis='index')
        return mean

    @property
    def std(self):
        """Series СКО доходности"""
        return super().std * self._ml_data.std


if __name__ == '__main__':
    import trading

    port = Portfolio(date=trading.DATE,
                     cash=trading.CASH,
                     positions=trading.POSITIONS)
    metrics = MLReturnsMetrics(port)
    print(metrics)
