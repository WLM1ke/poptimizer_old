"""Основные метрики доходности на базе ML-модели"""
import numpy as np
import pandas as pd

from local import moex
from metrics.portfolio import CASH, PORTFOLIO, Portfolio
from metrics.returns_metrics import AbstractReturnsMetrics
from ml.returns.manager import ReturnsMLDataManager


class MLReturnsMetrics(AbstractReturnsMetrics):
    def __init__(self, portfolio: Portfolio):
        super().__init__(portfolio)
        manager = ReturnsMLDataManager(portfolio.positions[:-2], pd.Timestamp(portfolio.date))
        self._ml_data = manager.value

    def __str__(self):
        return super().__str__() + f'\n\nСредняя корреляция - {self._mean_corr:.2%}'

    @property
    def returns(self):
        """Доходности составляющих портфеля и самого портфеля"""
        portfolio = self._portfolio
        returns = moex.log_returns_with_div(portfolio.positions[:-2], pd.Timestamp(portfolio.date))
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
    def _mean_corr(self):
        """Усредненная корреляция между позициями"""
        weighted_std = self.std * self._portfolio.weight
        std_portfolio = weighted_std[PORTFOLIO]
        std_positions = weighted_std.iloc[:-1].values
        std_matrix = np.matmul(std_positions.reshape(-1, 1), std_positions.reshape(1, -1))
        trace = np.trace(std_matrix)
        return (std_portfolio ** 2 - trace) / (np.sum(std_matrix) - trace)

    @property
    def beta(self):
        """Бета рассчитывается на основе усредненной корреляции между отдельными позициями"""
        weighted_std = self.std * self._portfolio.weight
        std_portfolio = weighted_std[PORTFOLIO]
        std_positions = weighted_std.iloc[:-1].values
        beta = np.matmul(self.std.iloc[:-1].values.reshape(-1, 1), std_positions.reshape(1, -1))
        std_diag = np.diag(np.diag(beta))
        mean_corr = self._mean_corr
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
    dsr = (metrics.mean - metrics.beta * metrics.mean.iloc[-1]) / metrics.std.iloc[-1]
    print(dsr.sort_values(ascending=False))

    print(metrics.mean.iloc[-1] / metrics.std.iloc[-1])
    t = 2 / (12 ** 0.5)
    mean_gradient = metrics.mean - metrics.mean.iloc[-1]
    risk_gradient = metrics.std.iloc[-1] * (metrics.beta - 1)
    gr = (mean_gradient - t * risk_gradient) / (t * metrics.std.iloc[-1])
    print(t)
    print(gr.sort_values(ascending=False))
