"""Реализация класса портфеля"""

from functools import lru_cache

import numpy as np
import pandas as pd

from portfolio_optimizer import local
from portfolio_optimizer.settings import PORTFOLIO, CASH, PRICE, LOTS, VALUE, WEIGHT, LOT_SIZE


class Portfolio:
    """Базовый класс портфеля

    Хранит информацию на отчетную дату о денежных средствах и количестве лотов для набора тикеров из словаря
    Для проверки может быть передана стоимость портфеля, которая не должна сильно отличаться от расчетной стоимости, на
    основе котировок на отчетную дату
    Отчетная дата должна быть торговым днем
    """
    def __init__(self, date: str, cash: float, positions: dict, value: float = None):
        self._date = pd.to_datetime(date).date()
        self._positions = tuple(sorted(positions.keys())) + (CASH, PORTFOLIO)
        data = [positions[ticker] for ticker in self._positions[:-2]] + [cash, 1]
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
        df.columns = [LOT_SIZE, LOTS, PRICE, VALUE, WEIGHT]
        return (f'\nПОРТФЕЛЬ'
                f'\n'
                f'\nДата - {self._date}'
                f'\n'
                f'\n{df}')

    @property
    def date(self):
        """Дата портфеля"""
        return self._date

    @property
    def positions(self):
        """Кортеж позиций портфеля - является индексом всех характеристик портфеля

        В начале идут упорядоченные по алфавиту тикеры, а потом CASH и PORTFOLIO
        """
        return self._positions

    @property
    @lru_cache(maxsize=1)
    def lot_size(self):
        """Размер лотов отдельных позиций

        Размер лота для CASH и PORTFOLIO 1
        """
        lot_size = pd.Series(index=self._positions)
        lot_size.iloc[:-2] = local.lot_size(self._positions[:-2])
        lot_size[CASH:PORTFOLIO] = (1, 1)
        return lot_size

    @property
    def lots(self):
        """Количество лотов для отдельных позиций

        Количество лотов для CASH и PORTFOLIO количество денег и 1"""
        return self._lots

    @property
    def shares(self):
        """Количество акций для отдельных позиций"""
        return self.lot_size * self._lots

    @property
    @lru_cache(maxsize=1)
    def price(self):
        """Цены акций на дату портфеля для отдельных позиций"""
        price = pd.Series(index=self._positions)
        tickers = self._positions[:-2]
        prices = local.prices(tickers)
        prices = prices.loc[:self._date]
        for ticker in tickers:
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
        return df

    @property
    def weight(self):
        """Вес отдельных позиций в стоимости портфеля"""
        df = self.value / self.value[PORTFOLIO]
        return df


if __name__ == '__main__':
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123),
                     value=3_699_111.41)
    print(port)
