"""Реализация класса портфеля."""

import numpy as np
import pandas as pd

from portfolio_optimizer import local
from portfolio_optimizer.settings import PORTFOLIO, CASH, PRICE, LOTS, VALUE, WEIGHT


class Portfolio:
    """Базовый класс портфеля

    Хранит информацию на отчетную дату о денежных средствах и количестве лотов для набора тикеров из словаря
    Для проверки может быть передана стоимость портфеля, которая не должна сильно отличаться от расчетной стоимости, на
    основе котировок на отчетную дату
    """
    def __init__(self, date: str, cash: float, positions: dict, value: float = None):
        self._date = pd.to_datetime(date).date()
        self._tickers = tuple(sorted(positions.keys()))
        self._positions = self._tickers + (CASH, PORTFOLIO)
        data = [positions[ticker] for ticker in self._tickers] + [cash, 1]
        self._lots = pd.Series(data=data, index=self._positions, name=LOTS)
        if value:
            if not np.isclose(self.value[PORTFOLIO], value):
                raise ValueError(f'Введенная стоимость портфеля {value} '
                                 f'не равна расчетной {self.value[PORTFOLIO]}.')

    def __str__(self):
        df = pd.concat([self.lot_size,
                        self.lots,
                        self.price,
                        self.value,
                        self.weight], axis='columns')

        return f'\n\nДата портфеля - {self._date}\n\n{df}'

    @property
    def date(self):
        """Дата портфеля"""
        return self._date

    @property
    def tickers(self):
        """Кортеж тикеров портфеля"""
        return self._tickers

    @property
    def positions(self):
        """Кортеж позиций портфеля"""
        return self._positions

    @property
    def lot_size(self):
        """Размер лотов"""
        lot_size = local.lot_size(self._tickers)
        lot_size = lot_size.reindex(self._positions)
        lot_size[CASH:PORTFOLIO] = (1, 1)
        return lot_size

    @property
    def lots(self):
        """Количество лотов"""
        return self._lots

    @property
    def shares(self):
        """Количество акций"""
        return self.lot_size * self._lots

    @property
    def price(self):
        """Цены акций на дату"""
        price = pd.Series(index=self._positions, name=PRICE)
        prices = local.prices(self._tickers)
        prices = prices.loc[:self._date, :]
        for ticker in self._tickers:
            prices_column = prices[ticker]
            index = prices_column.last_valid_index()
            price[ticker] = prices_column[index]
        price[CASH] = 1
        price[PORTFOLIO] = (self.shares[:-1] * price[:-1]).sum(axis='index')
        return price

    @property
    def value(self):
        """Стоимость отдельных позиций"""
        df = self.shares * self.price
        df.name = VALUE
        return df

    @property
    def weight(self):
        """Доля в стоимости портфеля отдельных позиций"""
        df = self.value / self.value[PORTFOLIO]
        df.name = WEIGHT
        return df

    def change_date(self, date: str):
        """Изменяет дату портфеля"""
        self._date = pd.to_datetime(date).date()


if __name__ == '__main__':
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123),
                     value=3_699_111.41)
    print(port)
