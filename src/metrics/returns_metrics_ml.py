"""Основные метрики доходности на базе ML-модели"""
from functools import lru_cache

import numpy as np
import pandas as pd

from local import moex
from metrics.portfolio import CASH
from metrics.portfolio import PORTFOLIO
from metrics.portfolio import Portfolio
from metrics.returns_metrics import AbstractReturnsMetrics
from ml.returns.manager import ReturnsMLDataManager
from settings import T_SCORE

MONTH_TO_OPTIMIZE = 7


class MLReturnsMetrics(AbstractReturnsMetrics):
    def __init__(self, portfolio: Portfolio):
        super().__init__(portfolio)
        manager = ReturnsMLDataManager(portfolio.positions[:-2], pd.Timestamp(portfolio.date))
        self._ml_data = manager.value

    def __str__(self):
        frames = [self.mean,
            self.std,
            self.beta,
            self.draw_down,
            self.lower_bound,
            self.gradient]
        df = pd.concat(frames, axis=1)
        df.columns = ['MEAN', 'STD', 'BETA', 'DRAW_DOWN', 'LOWER_BOUND', 'GRADIENT']
        std_at_draw_down = (T_SCORE / 2) * (self.std[PORTFOLIO] ** 2 / self.mean[PORTFOLIO])
        return (f'\nКЛЮЧЕВЫЕ МЕТРИКИ ДОХОДНОСТИ'
                f'\n'
                f'\nКонстанта сглаживания - {self.decay:.4f}'
                f'\nВремя до максимальной просадки - {self.time_to_draw_down:.1f}'
                f'\nСКО стоимости портфеля около максимума просадки - {std_at_draw_down:.4f} /'
                f' {std_at_draw_down * self._portfolio.value[PORTFOLIO]:.0f}'
                f'\n'
                f'\n{df}'
                f'\n'
                f'\nСредняя корреляция - {self._mean_corr:.2%}')

    @property
    @lru_cache(maxsize=1)
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
        return mean * 12

    @property
    @lru_cache(maxsize=1)
    def std(self):
        """Series СКО доходности"""
        return super().std * self._ml_data.std * (12 ** 0.5)

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

    @property
    def lower_bound(self):
        """Рассчитывает вклад в нижнюю границу доверительного интервала для дивидендной доходности

        Используемая t-статистика берется из файла настроек

        Для оптимизированных портфелей, нижняя граница доверительного интервала выше, чем у отдельных позиций
        """
        scale = MONTH_TO_OPTIMIZE / 12
        lower_bound = self.mean * scale - T_SCORE * self.std[PORTFOLIO] * (scale ** 0.5) * self.beta
        return lower_bound

    @property
    def gradient(self):
        """Рассчитывает производную нижней границы по доле актива в портфеле

        В общем случае равна (m - mp) - t * sp * (b - 1), m и mp - доходность актива и портфеля, соответственно,
        t - t-статистика, sp - СКО портфеля, b - бета актива

        Долю актива с максимальным градиентом необходимо наращивать, а с минимальным сокращать. Так как важную роль в
        градиенте играет бета, то во многих случаях выгодно наращивать долю не той бумаги, у которой самая высокая
        нижняя граница, а той у которой достаточно низкая бета при высокой дивидендной доходности

        При правильной реализации взвешенный по долям отдельных позиций градиент равен градиенту по портфелю в целом и
        равен 0
        """
        scale = MONTH_TO_OPTIMIZE / 12
        mean_gradient = (self.mean - self.mean[PORTFOLIO]) * scale
        risk_gradient = self.std[PORTFOLIO] * (self.beta - 1) * (scale ** 0.5)
        return mean_gradient - T_SCORE * risk_gradient

    @property
    def time_to_draw_down(self):
        """Время до ожидаемого максимального падения

        t = ((t_score * s) / (2 * m)) ** 2
        """
        return (self.std[PORTFOLIO] * T_SCORE / 2 / self.mean[PORTFOLIO]) ** 2 * 12

    @property
    def std_at_draw_down(self):
        """СКО стоимости портфеля в момент оптимизации
        """
        return self.std[PORTFOLIO] * (MONTH_TO_OPTIMIZE / 12) ** 0.5


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
    mean_gradient_ = metrics.mean - metrics.mean.iloc[-1]
    risk_gradient_ = metrics.std.iloc[-1] * (metrics.beta - 1)
    gr = (mean_gradient_ - t * risk_gradient_) / (t * metrics.std.iloc[-1])
    print(t)
    print(gr.sort_values(ascending=False))
