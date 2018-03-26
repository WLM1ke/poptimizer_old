import warnings

import numpy as np
import pandas as pd

from optimizer import getter
from optimizer.settings import LOTS
from optimizer.settings import PORTFOLIO, CASH, PRICE, WEIGHT, VALUE, LOT_SIZE


class Portfolio:
    """Базовый класс портфеля.

    Хранит информацию на отчетную дату о денежных средствах и количестве лотов для набора тикеров.
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
        self.tickers = sorted(positions.keys())
        self.cash_and_tickers = self.tickers + [CASH]
        self._create_df(cash)
        self._fill_lots(positions)
        self.prices = None
        self._fill_price()
        self._fill_value()
        if value:
            if not np.isclose(self.df.loc[PORTFOLIO, VALUE], value):
                raise ValueError(f'Введенная стоимость портфеля {value} '
                                 f'не равна расчетной {self.df.loc[PORTFOLIO, VALUE]}.')

    def __str__(self):
        return f'\nДата портфеля - {self.date}\n\n{self.df}'

    def _create_df(self, cash):
        """Создает DataFrame:

        Строки - тикеры, CASH и PORTFOLIO.
        Столбцы - размер лота, количество лотов, цена, стоимость и вес.

        Размер лота, количество лотов и цена:
        CASH - 1, денежные средства и 1.
        PORTFOLIO - 1, 1, а цена может быть заполнена только после расчета стоимости отдельных позиций.
        """
        df = getter.security_info(self.tickers)
        rows = df.index.append(pd.Index([CASH, PORTFOLIO]))
        self.df = df.reindex(index=rows, columns=self._COLUMNS, fill_value=0)
        self.df.loc[CASH, [LOT_SIZE, LOTS, PRICE]] = [1, cash, 1]
        self.df.loc[PORTFOLIO, [LOT_SIZE, LOTS]] = [1, 1]

    def _fill_lots(self, positions):
        """Заполняет данные по количеству лотов для тикеров."""
        self.df.loc[self.tickers, LOTS] = [positions[ticker] for ticker in self.tickers]

    def _fill_price(self):
        """Заполняет цены на отчетную дату."""
        if self.prices is None:
            prices = getter.prices_history(self.tickers)
            self.prices = prices.fillna(method='ffill')
        date = self.date
        index = self.prices.index
        if date not in index:
            date = index[index.get_loc(date, method='ffill')].date()
            non_trading_date = (f'\n\nТорги не проводились {self.date} - '
                                f'будут использованы котировки предыдущей торговой даты {date}.\n')
            warnings.warn(non_trading_date)
        self.df.loc[self.tickers, PRICE] = self.prices.loc[date]

    def _fill_value(self):
        """Рассчитывает стоимость отдельных позиций и вызывает метод расчета стоимости портфеля."""
        value_components = self.df.loc[self.cash_and_tickers, [LOT_SIZE, LOTS, PRICE]]
        self.df.loc[self.cash_and_tickers, VALUE] = value_components.prod(axis=1)
        self._fill_portfolio_value()

    def _fill_portfolio_value(self):
        """Рассчитывает стоимость портфеля и запускает расчет весов отдельных позиций."""
        portfolio_value = self.df.loc[self.cash_and_tickers, VALUE].sum(axis=0)
        self.df.loc[PORTFOLIO, [PRICE, VALUE]] = [portfolio_value, portfolio_value]
        self._fill_weight()

    def _fill_weight(self):
        """Рассчитывает веса отдельных позиций."""
        self.df.loc[:, WEIGHT] = self.df[VALUE] / self.df.loc[PORTFOLIO, VALUE]

    def change_date(self, date: str):
        pass


if __name__ == '__main__':
    port = Portfolio(date='2018-03-24',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123),
                     value=3_742_615.21)
    print(port)
