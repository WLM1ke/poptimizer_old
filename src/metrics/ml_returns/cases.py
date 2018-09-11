"""Генератор примеров для обучения и предсказания ожидаемой доходности"""
import pandas as pd
from pandas.tseries.offsets import BDay

from local import moex, dividends
from utils import aggregation

T2 = 2


class ReturnsCasesIterator:
    def __init__(self, tickers: tuple, last_date: pd.Timestamp, months: int):
        self._tickers = tickers
        self._last_date = last_date
        self._months = months
        self._returns = self._make_returns()

    def _make_returns(self):
        """Создает доходности с учетом дивидендов"""
        prices = moex.prices_t2(self._tickers).fillna(method='ffill', axis='index')
        monthly_prices = prices.groupby(by=aggregation.monthly_aggregation_func(self._last_date)).last()
        monthly_prices = monthly_prices.loc[:self._last_date]

        def t2_shift(x):
            """Рассчитывает T-2 дату

            Если дата не содержится индексе цен, то необходимо найти предыдущую из индекса цен. После этого взять
            сдвинутую на 2 назад дату. Если дата находится в будущем за пределом истории котировок, то достаточно
            сдвинуть на 2 бизнес дня назад - упрощенный подход, который может не корректно работать из-за праздников
            """
            if x <= prices.index[-1]:
                index = prices.index.get_loc(x, 'ffill')
                return prices.index[index - T2]
            return x - T2 * BDay()

        div = dividends.dividends(self._tickers).loc[monthly_prices.index[0]:, :]
        div.index = div.index.map(t2_shift)
        monthly_dividends = div.groupby(by=aggregation.monthly_aggregation_func(self._last_date)).sum()
        # В некоторые месяцы не платятся дивиденды - без этого буду NaN при расчете доходностей
        monthly_dividends = monthly_dividends.reindex(index=monthly_prices.index, fill_value=0)
        returns = (monthly_prices + monthly_dividends) / monthly_prices.shift(1) - 1
        return returns


if __name__ == '__main__':
    try:
        from trading import POSITIONS, DATE
    except ModuleNotFoundError:
        POSITIONS = ['AKRN']
        DATE = '2018-09-06'
    iter_ = ReturnsCasesIterator(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), 12)
    describe = iter_._returns.describe().T
    print(describe)
    print(describe['mean'] / describe['std'] * (12 ** 0.5))
    print(describe['mean'].mean() / (describe['std'] ** 2).mean() ** 0.5 * (12 ** 0.5))
