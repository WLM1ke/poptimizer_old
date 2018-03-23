import time

import numpy as np
import pandas as pd

from optimizer import getter
from optimizer.settings import LOTS
from optimizer.settings import PORTFOLIO, CASH, LAST_VALUE, LAST_WEIGHT, PRICE, WEIGHT, VALUE, LOT_SIZE, LAST_PRICE


class Portfolio:
    """Базовый класс портфеля.

    Хранит общую информацию по входящим тикерам, рассчитывает стоимость и доли текущие  ина момент формирования.
    """
    _COLUMNS = [LOT_SIZE, LOTS, PRICE, VALUE, WEIGHT, LAST_PRICE, LAST_VALUE, LAST_WEIGHT]

    def __init__(self, date: str, cash: float, positions: dict, value: float = None):
        self.date = pd.to_datetime(date).date()
        self.tickers = sorted(positions.keys())
        self.cash_and_tickers = self.tickers + [CASH]
        self._create_df(cash)
        self._fill_lots(positions)
        self._fill_price_and_value()
        if value:
            if not np.isclose(self.df.loc[PORTFOLIO, VALUE], value):
                raise ValueError(f'Введенная стоимость портфеля {value}'
                                 f' не равна расчетной {self.df.loc[PORTFOLIO, VALUE]}.')
        self._fill_weight()
        self.update_last_price()

    def __str__(self):
        return f'\nДата портфеля - {self.date}\n\n{self.df}'

    def _create_df(self, cash):
        df = getter.security_info(self.tickers)
        rows = df.index.append(pd.Index([CASH, PORTFOLIO]))
        self.df = df.reindex(index=rows, columns=self._COLUMNS, fill_value=0)
        self.df.loc[[CASH, PORTFOLIO], LOT_SIZE] = [1, 1]
        self.df.loc[[CASH, PORTFOLIO], LOTS] = [cash, 1]
        self.df.loc[CASH, [PRICE, LAST_PRICE]] = 1

    def _fill_lots(self, positions):
        self.df.loc[self.tickers, LOTS] = [positions[ticker] for ticker in self.tickers]

    def _fill_price_and_value(self):
        prices = getter.prices_history(self.tickers)
        self.prices = prices.fillna(method='ffill')
        self.df.loc[self.tickers, PRICE] = self.prices.loc[self.date]
        value_components = self.df.loc[self.cash_and_tickers, [LOT_SIZE, LOTS, PRICE]]
        self.df.loc[self.cash_and_tickers, VALUE] = value_components.prod(axis=1)
        value = self.df.loc[self.cash_and_tickers, VALUE].sum(axis=0)
        self.df.loc[PORTFOLIO, [PRICE, VALUE]] = [value, value]

    def _fill_weight(self):
        self.df.loc[:, WEIGHT] = self.df[VALUE] / self.df.loc[PORTFOLIO, VALUE]

    def update_last_price(self):
        last_prices = getter.last_prices(self.tickers)
        self.df.loc[self.tickers, LAST_PRICE] = last_prices.fillna(value=self.prices.iloc[-1, :])
        self._update_last_value()
        self._update_last_weight()

    def _update_last_value(self):
        value_components = self.df.loc[self.cash_and_tickers, [LOT_SIZE, LOTS, LAST_PRICE]]
        self.df.loc[self.cash_and_tickers, LAST_VALUE] = value_components.prod(axis=1)
        value = self.df.loc[self.cash_and_tickers, LAST_VALUE].sum(axis=0)
        self.df.loc[PORTFOLIO, [LAST_PRICE, LAST_VALUE]] = [value, value]

    def _update_last_weight(self):
        self.df.loc[:, LAST_WEIGHT] = self.df[LAST_VALUE] / self.df.loc[PORTFOLIO, LAST_VALUE]


if __name__ == '__main__':
    port = Portfolio(date='2018-03-21',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123),
                     value=3_728_568.41)
    print(port)
    time.sleep(10)
    port.update_last_price()
    print(port)
