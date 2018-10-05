"""Основные метрики доходности на базе ML-модели"""
import numpy as np
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
        returns = cases.log_returns_with_div(portfolio.positions[:-2], pd.Timestamp(portfolio.date)).fillna(0)
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

    @property
    def beta(self):
        weighted_std = self.std * self._portfolio.weight
        std_portfolio = weighted_std[PORTFOLIO]
        std_positions = weighted_std.iloc[:-1].to_frame().values
        std_matrix = np.matmul(std_positions, std_positions.reshape(1, -1))
        trace = np.trace(std_matrix)
        mean_corr = (std_portfolio ** 2 - trace) / (np.sum(std_matrix) - trace)
        beta = np.matmul(self.std.iloc[:-1].to_frame().values, std_positions.reshape(1, -1))
        std_diag = np.diag(np.diag(beta))
        beta = np.sum(((beta - std_diag) * mean_corr + std_diag) / std_portfolio ** 2, axis=1)
        beta = pd.Series(beta, index=weighted_std.index[:-1])
        beta[PORTFOLIO] = 1
        return beta


if __name__ == '__main__':
    import trading

    port = Portfolio(date=trading.DATE,
                     cash=trading.CASH,
                     positions=trading.POSITIONS)
    metrics = MLReturnsMetrics(port)
    print(metrics)
