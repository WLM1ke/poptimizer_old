"""Реализация основных метрик доходности"""

from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import optimize, stats

import local
from portfolio import Portfolio, CASH, PORTFOLIO
from settings import T_SCORE

# Интервал поиска константы сглаживания
BOUNDS = (0.0, 1.0)
# Интервал обычного расположения константы сглаживания - при необходимости можно расширить
BRACKET = (0.84, 0.91)
# Сколько процентов данных отбрасывается при оптимизации llh, чтобы экспоненциальное сглаживание стабилизировалось
SAMPLE_DROP_OUT = 0.20


class ReturnsMetrics:
    """Метрики доходности рассчитываются на дату формирования портфеля для месячных таймфреймов"""

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._decay = None
        self.fit()

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
                f'\nНачальная дата для расчета сглаживания - {self.returns.index[self._llh_start()].date()}'
                f'\nКонстанта сглаживания - {self._decay:.4f}'
                f'\nВремя до максимальной просадки - {self.time_to_draw_down:.1f}'
                f'\nСКО стоимости портфеля около максимума просадки - {self.std_at_draw_down:.4f}'
                f'\n'
                f'\n{df}')

    @property
    def monthly_prices(self):
        """Формирует DataFrame цен с шагом в месяц

        Эти ряды цен служат для расчета всех дальнейших показателей
        """
        prices = local.prices(self._portfolio.positions[:-2])
        prices = prices[:self._portfolio.date].fillna(method='ffill')
        return prices.groupby(by=self._monthly_aggregation).last()

    def _monthly_aggregation(self, x: pd.Timestamp):
        """Приводит все даты к отчетному дню портфеля в месяце - используется для месячной агригации

        Если день больше отчетного, то день относится к следующему месяцу
        """
        portfolio_day = self._portfolio.date.day
        if x.day <= portfolio_day:
            return x + pd.DateOffset(day=portfolio_day)
        else:
            return x + pd.DateOffset(months=1, day=portfolio_day)

    @property
    @lru_cache(maxsize=1)
    def returns(self):
        """Доходности составляющих портфеля и самого портфеля

        Доходность кэша - ноль
        Доходность портфеля рассчитывается на основе долей на отчетную дату портфеля
        """
        returns = self.monthly_prices.pct_change()
        # Для первого периода доходность отсутствует
        returns = returns.iloc[1:]
        returns = returns.reindex(columns=self._portfolio.positions)
        returns = returns.fillna(0)
        weight = self._portfolio.weight.iloc[:-2].transpose()
        returns[PORTFOLIO] = returns.iloc[:, :-2].multiply(weight).sum(axis=1)
        return returns

    def fit(self):
        """Осуществляет поиск константы сглаживания методом максимального правдоподобия"""
        result = optimize.minimize_scalar(self._llh,
                                          bracket=BRACKET,
                                          bounds=BOUNDS,
                                          method='Bounded')
        if result.success:
            decay = result.x
            if BRACKET[0] < decay < BRACKET[1]:
                self._decay = decay
            else:
                raise ValueError(f'Константа сглаживания {decay} вне интервала {BRACKET}')
        else:
            raise ValueError('Оптимальная константа сглаживания не найдена')

    def _llh_start(self):
        """Значение с которого считается llh"""
        return int(len(self.returns) * SAMPLE_DROP_OUT)

    def _llh(self, decay: float):
        """-llh для портфеля

        Используется экспоненциальное сглаживание и предположение нормальности
        """
        ewm = self.returns[PORTFOLIO].ewm(alpha=1 - decay)
        std = ewm.std()
        mean = ewm.mean()
        x = self.returns[PORTFOLIO].shift(periods=-1)
        start = self._llh_start()
        # Первые значения отбрасываются для стабилизации сглаживания, а для последнего значения нет llh
        llh = stats.norm.logpdf(x.iloc[start:-1],
                                mean.iloc[start:-1],
                                std.iloc[start:-1])
        return - llh.sum()

    @property
    def decay(self):
        """Константа сглаживания

        Первоначально вычисляется методом максимального правдоподобия при создании объекта. Если портфель изменен, можно
        уточнить ее значение вызовом метода fit(). Обычно она меняется не сильно, и повторные вызовы носят
        необязательный характер"""
        return self._decay

    @property
    def mean(self):
        """Ожидаемая доходность отдельных позиций и портфеля

        Используется простой процесс экспоненциального сглаживания
        """
        return self.returns.ewm(alpha=1 - self.decay).mean().iloc[-1]

    @property
    def std(self):
        """СКО отдельных позиций и портфеля

        Используется простой процесс экспоненциального сглаживания
        """
        return self.returns.ewm(alpha=1 - self.decay).std().iloc[-1]

    @property
    def beta(self):
        """Беты отдельных позиций и портфеля

        При расчете беты используется классическая формула cov(r,rp) / var(rp), где r и rp - доходность актива и
        портфеля, соответственно, при этом используется простой процесс экспоненциального сглаживания
        """
        ewm = self.returns.ewm(alpha=1 - self.decay)
        ewm_cov = ewm.cov(self.returns[PORTFOLIO])
        return ewm_cov.multiply(1 / ewm_cov[PORTFOLIO], axis='index').iloc[-1]

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


if __name__ == '__main__':
    pos = dict(MSTT=4650,
               LSNGP=162,
               MTSS=749,
               AKRN=795,
               GMKN=223)
    port = Portfolio(date='2018-03-19',
                     cash=1_415_988,
                     positions=pos)
    metrics = ReturnsMetrics(port)
    print(metrics)
