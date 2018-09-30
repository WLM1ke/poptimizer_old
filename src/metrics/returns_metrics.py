"""Абстрактный класс основных метрик доходности"""
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from metrics.portfolio import Portfolio, CASH, PORTFOLIO
from settings import T_SCORE


class AbstractReturnsMetrics(ABC):
    """Метрики доходности рассчитываются на дату формирования портфеля для месячных таймфреймов"""

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio

    def __str__(self):
        frames = [self.mean,
                  self.std,
                  self.beta,
                  self.draw_down,
                  self.gradient]
        df = pd.concat(frames, axis=1)
        df.columns = ['MEAN', 'STD', 'BETA', 'DRAW_DOWN', 'GRADIENT']
        return (f'\nКЛЮЧЕВЫЕ МЕТРИКИ ДОХОДНОСТИ'
                f'\n'
                f'\nВремя до максимальной просадки - {self.time_to_draw_down:.1f}'
                f'\nСКО стоимости портфеля около максимума просадки - {self.std_at_draw_down:.4f}'
                f'\n'
                f'\n{df}')

    @property
    @abstractmethod
    def mean(self):
        """Series матожидания доходности"""
        raise NotImplementedError

    @property
    @abstractmethod
    def std(self):
        """Series СКО доходности"""
        raise NotImplementedError

    @property
    @abstractmethod
    def beta(self):
        """Беты отдельных позиций и портфеля"""
        raise NotImplementedError

    @property
    def draw_down(self):
        """Ожидаемый draw down

        Динамика минимальной стоимости портфеля может быть описана следующим выражением:
        m * t - t_score * s * (t ** 0.5)
        Минимум при положительных m достигается:
        t = ((t_score * s) / (2 * m)) ** 2
        Соответственно, максимальная просадка:
        draw_down = - (t_score * s) ** 2 / (4 * m)
        t-статистика берется из файла настроек
        """
        std = self.std
        mean = self.mean
        draw_down = - (T_SCORE * std) ** 2 / (4 * mean)
        # Если ожидаемая доходность меньше нуля, то просадка не определена
        draw_down[mean < 0] = np.nan
        # Для кэша потери нулевые
        draw_down[CASH] = 0
        return draw_down

    @property
    def gradient(self):
        """Производная нижней границы портфеля по доле актива в портфеле

        Можно показать, что градиент равен:
        (t_score / 2) ** 2 * (sp / mp) ** 2 * (m - mp - 2 * mp * (b - 1)), где m и mp - доходность актива и портфеля,
        соответственно, sp - СКО портфеля, b - бета актива
        Долю актива с максимальным градиентом необходимо наращивать, а с минимальным сокращать
        При правильной реализации взвешенный по долям отдельных позиций градиент равен градиенту по портфелю в целом и
        равен 0
        """
        std_p = self.std[PORTFOLIO]
        mean = self.mean
        mean_p = mean[PORTFOLIO]
        beta = self.beta
        return (T_SCORE / 2) ** 2 * (std_p / mean_p) ** 2 * (mean - mean_p - 2 * mean_p * (beta - 1))

    @property
    def time_to_draw_down(self):
        """Время до ожидаемого максимального падения

        t = ((t_score * s) / (2 * m)) ** 2
        """
        return (self.std[PORTFOLIO] * T_SCORE / 2 / self.mean[PORTFOLIO]) ** 2

    @property
    def std_at_draw_down(self):
        """СКО стоимости портфеля в момент наибольшей просадки

        S = s * (t ** 0.5) = s * ((t_score * s) / (2 * m)) = (t_score / 2) * (s ** 2 / m)
        """
        return (T_SCORE / 2) * (self.std[PORTFOLIO] ** 2 / self.mean[PORTFOLIO])
