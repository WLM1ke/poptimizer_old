"""Реализация основных метрик доходности"""

from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import optimize, stats

from portfolio_optimizer import local
from portfolio_optimizer.portfolio import Portfolio
from portfolio_optimizer.settings import PORTFOLIO, T_SCORE, CASH

# Интервал поиска константы сглаживания
BOUNDS = (0.0, 1.0)
# Интервал обычного расположения константы сглаживания - при необходимости можно расширить
BRACKET = (0.86, 0.92)
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
                f'\n'
                f'\n{df}')

    @property
    def monthly_prices(self):
        """Формирует DataFrame цен с шагом в месяц

        Эти ряды цен служат для расчета всех дальнейших показателей
        """
        prices = local.prices(self._portfolio.positions[:-2]).fillna(method='ffill')
        monthly_index = self._monthly_index(prices.index)
        return prices.loc[monthly_index]

    def _monthly_index(self, index):
        """Формирует массив дат от начального исторических данных до даты портфеля """
        portfolio_date = self._portfolio.date.timetuple()[:3]
        reversed_monthly_index = []
        for date in reversed(index):
            if portfolio_date < date.timetuple()[:3]:
                continue
            else:
                reversed_monthly_index.append(date)
                if portfolio_date[1] != 1:
                    portfolio_date = portfolio_date[0], portfolio_date[1] - 1, portfolio_date[2]
                else:
                    portfolio_date = portfolio_date[0] - 1, 12, portfolio_date[2]
        return reversed(reversed_monthly_index)

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
        """-llh для портфеля с отброшенными константами

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

        При расчет беты используется классическая формула cov(r,rp) / var(rp), где r и rp - доходность актива и
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


if __name__ == '__main__':
    pos = dict(VSMO=133,
               MVID=264,
               LKOH=123,
               AFLT=5,
               KBTK=9)
    port = Portfolio(date='2018-04-05',
                     cash=2749.64,
                     positions=pos)
    metrics = ReturnsMetrics(port)
    print(metrics)
