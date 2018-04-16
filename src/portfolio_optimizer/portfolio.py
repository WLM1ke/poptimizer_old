"""Реализация класса портфеля."""

import warnings

import numpy as np
import pandas as pd

from portfolio_optimizer import local
from portfolio_optimizer.settings import LOTS
from portfolio_optimizer.settings import PORTFOLIO, CASH, PRICE, WEIGHT, VALUE, LOT_SIZE


class Portfolio:
    """Базовый класс портфеля.

    Хранит информацию на отчетную дату о денежных средствах и количестве лотов для набора тикеров из словаря.
    Для проверки может быть передана стоимость портфеля, которая не должна сильно отличаться от расчетной стоимости, на
    основе котировок на отчетную дату.

    Рассчитывает стоимость портфеля и отдельных позиций, а так же доли позиций в портфеле.

    Атрибуты:

    date: datetime.datetime
        Дата, на которую рассчитаны параметры портфеля.

    df: pandas.DataFrame
        Все метрики портфеля.

    prices: pandas.DataFrame
        Ряды цен для тикеров портфеля. Отсутствующие значения заменены последними предыдущими.

    Методы:

    change_date(date: str):
        Изменяет дату портфеля, цены и пересчитывает все остальные параметры.
    """
    _COLUMNS = [LOT_SIZE, LOTS, PRICE, VALUE, WEIGHT]

    def __init__(self, date: str, cash: float, positions: dict, value: float = None):
        self.date = pd.to_datetime(date).date()
        self._tickers = sorted(positions.keys())
        self.cash_and_tickers = self._tickers + [CASH]
        self._create_df(cash)
        self._fill_lots(positions)
        self.prices = None
        self._fill_price()
        self._fill_value()
        if value:
            if not np.isclose(self._df.loc[PORTFOLIO, VALUE], value):
                raise ValueError(f'Введенная стоимость портфеля {value} '
                                 f'не равна расчетной {self._df.loc[PORTFOLIO, VALUE]}.')

    def __str__(self):
        return f'\n\nДата портфеля - {self.date}\n\n{self._df}'

    def _create_df(self, cash):
        """Создает DataFrame:

        Строки - тикеры, CASH и PORTFOLIO.
        Столбцы - размер лота, количество лотов, цена, стоимость и вес.

        Размер лота, количество лотов и цена:
        CASH - 1, денежные средства и 1.
        PORTFOLIO - 1, 1, а цена может быть заполнена только после расчета стоимости отдельных позиций.
        """
        df = local.securities_info(self._tickers)
        rows = df.index.append(pd.Index([CASH, PORTFOLIO]))
        self._df = df.reindex(index=rows, columns=self._COLUMNS, fill_value=0)
        self._df.loc[CASH, [LOT_SIZE, LOTS, PRICE]] = [1, cash, 1]
        self._df.loc[PORTFOLIO, [LOT_SIZE, LOTS]] = [1, 1]

    def _fill_lots(self, positions):
        """Заполняет данные по количеству лотов для тикеров."""
        self._df.loc[self._tickers, LOTS] = [positions[ticker] for ticker in self._tickers]

    def _fill_price(self):
        """Заполняет цены на отчетную дату или предыдущую торговую."""
        if self.prices is None:
            prices = local.prices(self._tickers)
            self.prices = prices.fillna(method='ffill')
        date = self.date
        index = self.prices.index
        if date not in index:
            date = index[index.get_loc(date, method='ffill')].date()
            non_trading_date = (f'\n\nТорги не проводились {self.date} - '
                                f'будут использованы котировки предыдущей торговой даты {date}.\n')
            warnings.warn(non_trading_date)
        self._df.loc[self._tickers, PRICE] = self.prices.loc[date]

    def _fill_value(self):
        """Рассчитывает стоимость отдельных позиций и вызывает метод расчета стоимости портфеля."""
        value_components = self._df.loc[self.cash_and_tickers, [LOT_SIZE, LOTS, PRICE]]
        self._df.loc[self.cash_and_tickers, VALUE] = value_components.prod(axis=1)
        self._fill_portfolio_value()

    def _fill_portfolio_value(self):
        """Рассчитывает стоимость портфеля и запускает расчет весов отдельных позиций."""
        portfolio_value = self._df.loc[self.cash_and_tickers, VALUE].sum(axis=0)
        self._df.loc[PORTFOLIO, [PRICE, VALUE]] = [portfolio_value, portfolio_value]
        self._fill_weight()

    def _fill_weight(self):
        """Рассчитывает веса отдельных позиций."""
        self._df.loc[:, WEIGHT] = self._df[VALUE] / self._df.loc[PORTFOLIO, VALUE]

    def change_date(self, date: str):
        """Изменяет дату портфеля и пересчитывает значения всех показателей."""
        self.date = pd.to_datetime(date).date()
        self._fill_price()
        self._fill_value()

    @property
    def index(self):
        """Тикеров, кэш и портфель"""
        return self._df.index

    @property
    def tickers(self):
        """Тикеры портфеля"""
        return self._tickers

    @property
    def lot_size(self):
        """Размер лотов"""
        return self._df[LOT_SIZE]

    @property
    def lots(self):
        """Количество лотов"""
        return self._df[LOTS]

    @property
    def amount(self):
        """Количество акций"""
        return self._df[[LOT_SIZE, LOTS]].prod(axis=1)

    @property
    def price(self):
        """Цены акций на отчетную дату"""
        return self._df[PRICE]

    @property
    def value(self):
        """Стоимость отдельных позиций"""
        return self._df[VALUE]

    @property
    def weight(self):
        """Доля в стоимости портфеля отдельных позиций"""
        return self._df[WEIGHT]


if __name__ == '__main__':
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123),
                     value=3_699_111.41)
    print(port)
    port.change_date('2018-03-25')
    print(port)
    print(Portfolio(date='2018-03-25',
                    cash=1000.21,
                    positions=dict(GAZP=682, VSMO=145, TTLK=123),
                    value=3_742_615.21))
