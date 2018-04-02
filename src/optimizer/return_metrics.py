"""Реализация основных метрик доходности"""

import numpy as np
import pandas as pd
from scipy import optimize

from optimizer.portfolio import Portfolio
from optimizer.settings import PORTFOLIO, T_SCORE, CASH

# Интервал поиска константы сглаживания
BRACKET = (0.85, 0.90)


class ReturnMetrics:
    """Метрики доходности рассчитываются на дату формирования портфеля для месячных таймфреймов"""

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._tickers = portfolio.index[:-2]
        self._decay = None
        self.fit()

    def __str__(self):
        frames = [self.mean,
                  self.std,
                  self.beta,
                  self.draw_down,
                  self.gradient_of_draw_down]
        columns = ['MEAN', 'STD', 'BETA', 'DRAW_DOWN', 'GRADIENT']
        df = pd.concat(frames, axis=1)
        df.columns = columns
        return (f'{self._portfolio}\n\n'
                f'Ключевые метрики доходности при константе сглаживания - '
                f'{self._decay:.4f}:\n\n{df}')

    @property
    def monthly_prices(self):
        """Формирует DataFrame цен с шагом в месяц

        Эти ряды цен служат для расчета всех дальнейших показателей
        """
        prices = self._portfolio.prices
        date_tuple = self._portfolio.date.timetuple()[:3]
        reversed_index = []
        for date in reversed(prices.index):
            if date_tuple < date.timetuple()[:3]:
                continue
            else:
                reversed_index.append(date)
                if date_tuple[1] != 1:
                    date_tuple = date_tuple[0], date_tuple[1] - 1, date_tuple[2]
                else:
                    date_tuple = date_tuple[0] - 1, 12, date_tuple[2]
        return prices.loc[reversed(reversed_index)]

    @property
    def returns(self):
        """Доходности составляющих портфеля и самого портфеля

        Доходность кэша - ноль
        Доходность портфеля рассчитывается на основе долей на отчетную дату портфеля
        """
        returns = self.monthly_prices.pct_change()
        # Для первого периода доходность отсутствует
        returns = returns.iloc[1:]
        returns = returns.reindex(columns=self._portfolio.index)
        returns = returns.fillna(0)
        weight = self._portfolio.weight[self._tickers].transpose()
        returns[PORTFOLIO] = returns[self._tickers].multiply(weight).sum(axis=1)
        return returns

    def fit(self):
        """Осуществляет поиск константы сглаживания методом максимального правдоподобия"""
        result = optimize.minimize_scalar(self._llh, bracket=BRACKET)
        if result.success:
            decay = result.x
            if BRACKET[0] < decay < BRACKET[1]:
                self._decay = decay
            else:
                raise ValueError(f'Константа сглаживания {decay} вне интервала {BRACKET}')
        else:
            raise ValueError('Оптимальная константа сглаживания не найдена')

    def _llh(self, decay):
        """-llh для портфеля с отброшенными константами

        Используется логарифмическое сглаживание и предположение нормальности.

        PDF = ((s * (2 * pi) ** 0,5) ** -1) * exp(- ((x - m) ** 2) / (2 * s ** 2))
        ln PDF = - ln s - 0,5 ln (2 * pi) - ((x - m) ** 2) / (2 * s ** 2)
        Если отбросить константы -ln PDF = ln s + ((x - m) ** 2) / (2 * s ** 2)
        """
        ewm = self.returns[PORTFOLIO].ewm(alpha=1 - decay)
        std = ewm.std()
        mean = ewm.mean()
        x = self.returns[PORTFOLIO].shift(periods=-1)
        llh = np.log(std) + ((x - mean) ** 2) / (2 * std ** 2)
        # TODO: сделать разумную обрезку
        return llh.iloc[100:].sum()

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
        # Если ожидаемая доходность меньше нуля, то потеряется весь капитал
        draw_down[mean < 0] = -1
        # Для потери нулевые
        draw_down[CASH] = 0
        return draw_down

    @property
    def gradient_of_draw_down(self):
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
    positions = dict(MSTT=8650,
                     RTKMP=1826,
                     UPRO=3370,
                     LKOH=2230,
                     MVID=3260)
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=positions)
    print(ReturnMetrics(port))
