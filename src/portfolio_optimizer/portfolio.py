"""Реализация класса портфеля"""

from functools import lru_cache

import numpy as np
import pandas as pd

from portfolio_optimizer import local
from portfolio_optimizer.settings import VOLUME_CUT_OFF
from portfolio_optimizer.web.labels import LOT_SIZE

CASH = 'CASH'
PORTFOLIO = 'PORTFOLIO'
LOTS = 'LOTS'
PRICE = 'PRICE'
VALUE = 'VALUE'
WEIGHT = 'WEIGHT'
VOLUME = 'VOLUME'


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
                        self.weight,
                        self.volume_factor], axis='columns')
        df.columns = [LOT_SIZE, LOTS, PRICE, VALUE, WEIGHT, VOLUME]
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

    @staticmethod
    def _last_price(column):
        """Последняя заполненная цена в колонке или 0, если вся колонка NaN"""
        last_index = column.last_valid_index()
        if last_index:
            return column[last_index]
        else:
            return 0

    @property
    @lru_cache(maxsize=1)
    def price(self):
        """Цены акций на дату портфеля для отдельных позиций"""
        tickers = self._positions[:-2]
        prices = local.prices(tickers)
        prices = prices.loc[:self._date]
        price = prices.apply(self._last_price)
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

    @property
    def volume_factor(self):
        """Понижающий коэффициент для акций с малым объемом оборотов

        Ликвидность в первом приближении убывает пропорционально квадрату оборота, что отражено в формулах расчета
        """
        last_volume = local.volumes(self.positions[:-2]).loc[self.date]
        volume_share_of_portfolio = last_volume * self.price[:-2] / self.value[PORTFOLIO]
        volume_factor = 1 - (VOLUME_CUT_OFF / volume_share_of_portfolio) ** 2
        volume_factor[volume_factor < 0] = 0
        return volume_factor.reindex(index=self.positions, fill_value=1)


if __name__ == '__main__':
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123, KUNF=0))
    print(port.price)
