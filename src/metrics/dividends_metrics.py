"""Абстрактный класс основных метрик дивидендного потока"""
from abc import ABC
from abc import abstractmethod

import pandas as pd

from metrics.portfolio import CASH
from metrics.portfolio import PORTFOLIO
from metrics.portfolio import Portfolio
from settings import T_SCORE

DIVIDENDS_YEARS = 5
DIVIDENDS_MONTHS = DIVIDENDS_YEARS * 12


class AbstractDividendsMetrics(ABC):
    """Реализует основные метрики дивидендного потока для портфеля в реальном посленалоговом исчислении"""

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio

    def __str__(self):
        frames = [self.mean,
                  self.std,
                  self.beta,
                  self.lower_bound,
                  self.gradient]
        df = pd.concat(frames, axis=1)
        df.columns = ['MEAN', 'STD', 'BETA', 'LOWER_BOUND', 'GRADIENT']
        return (f'\nКЛЮЧЕВЫЕ МЕТРИКИ ДИВИДЕНДОВ'
                f'\n'
                f'\nОжидаемые дивиденды - {self.expected_dividends:.0f}'
                f'\nМинимальные дивиденды дивиденды - {self.minimal_dividends:.0f}'
                f'\n'
                f'\n{df}')

    @property
    @abstractmethod
    def _tickers_real_after_tax_mean(self):
        """Series матожидание реальной посленалоговой дивидендной доходности только для тикеров без CASH и PORTFOLIO"""
        raise NotImplementedError

    @property
    def mean(self):
        """Матожидание дивидендной доходности по всем позициям портфеля"""
        mean = self._tickers_real_after_tax_mean
        mean[CASH] = 0
        weighted_mean = mean * self._portfolio.weight[mean.index]
        mean[PORTFOLIO] = weighted_mean.sum(axis='index')
        return mean

    @property
    @abstractmethod
    def _tickers_real_after_tax_std(self):
        """Series СКО реальной посленалоговой дивидендной доходности только для тикеров без CASH и PORTFOLIO"""
        raise NotImplementedError

    @property
    def std(self):
        """СКО дивидендной доходности по всем позициям портфеля

        СКО портфеля рассчитывается из допущения нулевой корреляции между дивидендами отдельных позиций. Допущение о
        нулевой корреляции необходимо в качестве простого приема регуляризации, так как число лет существенно меньше
        количества позиций. Данное допущение используется во всех дальнейших расчетах
        """
        std = self._tickers_real_after_tax_std
        std[CASH] = 0
        weighted_std = std * self._portfolio.weight[std.index]
        std[PORTFOLIO] = (weighted_std ** 2).sum(axis='index') ** 0.5
        return std

    @property
    def beta(self):
        """Беты дивидендных доходностей

        Традиционно бета равна cov(r,rp) / var(rp), где r и rp - доходность актива и портфеля, соответственно.
        При используемых допущениях можно показать, что бета равна w * var(r) / var(rp), где w - доля актива в портфеле

        При правильной реализации взвешенная по долям бета отдельных позиций равна бете портфеля и равна 1, а бета кэша
        равна 0
        """
        var = self.std ** 2
        return (self._portfolio.weight * var) / (var[PORTFOLIO])

    @property
    def lower_bound(self):
        """Рассчитывает вклад в нижнюю границу доверительного интервала для дивидендной доходности

        Используемая t-статистика берется из файла настроек

        Для оптимизированных портфелей, нижняя граница доверительного интервала выше, чем у отдельных позиций
        """
        lower_bound = self.mean - T_SCORE * self.std[PORTFOLIO] * self.beta
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
        mean_gradient = self.mean - self.mean[PORTFOLIO]
        risk_gradient = self.std[PORTFOLIO] * (self.beta - 1)
        return mean_gradient - T_SCORE * risk_gradient

    @property
    def expected_dividends(self):
        """Ожидаемые дивиденды по портфелю в рублевом выражении"""
        return self.mean[PORTFOLIO] * self._portfolio.value[PORTFOLIO]

    @property
    def minimal_dividends(self):
        """Ожидаемые дивиденды по портфелю в рублевом выражении по нижней границе доверительного интервала"""
        return self.lower_bound[PORTFOLIO] * self._portfolio.value[PORTFOLIO]
