"""Реализация основных метрик доходности"""

from functools import lru_cache

import pandas as pd
from scipy import optimize, stats

from local import moex
from metrics.portfolio import Portfolio, PORTFOLIO
# Интервал поиска константы сглаживания
from metrics.returns_metrics import AbstractReturnsMetrics

BOUNDS = (0.0, 1.0)
# Интервал обычного расположения константы сглаживания - при необходимости можно расширить
BRACKET = (0.84, 0.91)
# Сколько процентов данных отбрасывается при оптимизации llh, чтобы экспоненциальное сглаживание стабилизировалось
SAMPLE_DROP_OUT = 0.20


class BaseReturnsMetrics(AbstractReturnsMetrics):
    """Метрики доходности рассчитываются на дату формирования портфеля для месячных таймфреймов"""

    def __init__(self, portfolio: Portfolio):
        super().__init__(portfolio)
        self._decay = None
        self.fit()

    @property
    def monthly_prices(self):
        """Формирует DataFrame цен с шагом в месяц

        Эти ряды цен служат для расчета всех дальнейших показателей
        """
        prices = moex.prices(self._portfolio.positions[:-2])
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


if __name__ == '__main__':
    import trading

    port = Portfolio(date=trading.DATE,
                     cash=trading.CASH,
                     positions=trading.POSITIONS)
    metrics = BaseReturnsMetrics(port)
    print(metrics.std)
    print(metrics.std.median())
    print(len(trading.POSITIONS))
    print(metrics.std.median() / len(trading.POSITIONS) ** 0.5)
