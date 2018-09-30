"""Основные метрики доходности на базе ML-модели"""
import pandas as pd

from metrics.portfolio import CASH, PORTFOLIO, Portfolio
from metrics.returns_metrics import AbstractReturnsMetrics
from ml.returns.manager import ReturnsMLDataManager


class MLReturnsMetrics(AbstractReturnsMetrics):
    @property
    def mean(self):
        """Series матожидания доходности"""
        portfolio = self._portfolio
        manager = ReturnsMLDataManager(portfolio.positions[:-2],
                                       pd.Timestamp(portfolio.date))
        mean = manager.value.prediction_mean
        mean[CASH] = 0
        weighted_mean = mean * self._portfolio.weight[mean.index]
        mean[PORTFOLIO] = weighted_mean.sum(axis='index')
        return mean

    @property
    def std(self):
        """Series СКО доходности"""
        portfolio = self._portfolio
        manager = ReturnsMLDataManager(portfolio.positions[:-2],
                                       pd.Timestamp(portfolio.date))
        std = manager.value.prediction_std
        std[CASH] = 0
        weighted_std = std * self._portfolio.weight[std.index]
        std[PORTFOLIO] = (weighted_std ** 2).sum(axis='index') ** 0.5
        return std

    @property
    def beta(self):
        """Беты отдельных позиций и портфеля"""
        var = self.std ** 2
        return (self._portfolio.weight * var) / (var[PORTFOLIO])


if __name__ == '__main__':
    import trading

    port = Portfolio(date=trading.DATE,
                     cash=trading.CASH,
                     positions=trading.POSITIONS)
    metrics = MLReturnsMetrics(port)
    print(metrics)
