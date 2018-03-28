"""Реализация основных метрик дивидендного потока"""

import pandas as pd

from optimizer import getter
from optimizer.portfolio import Portfolio
from optimizer.settings import LOTS, LOT_SIZE, PORTFOLIO, AFTER_TAX, PRICE, WEIGHT


class DividendsMetrics:
    """Реализует основные метрики дивидендного потока для портфеля

    За основу берутся legacy dividends для интервала лет с first_year до last_year включительно
    """

    def __init__(self, portfolio: Portfolio, first_year: int, last_year: int):
        self._df = portfolio.df
        self._columns = list(range(first_year, last_year + 1))
        self._index = portfolio.df.index
        self._tickers = self._index[:-2]
        self._amount = portfolio.df[[LOT_SIZE, LOTS]].prod(axis=1)

    def nominal_pretax_dividends(self):
        """Дивиденды в номинальном выражении"""
        df = pd.DataFrame(0.0, index=self._index, columns=self._columns)
        df.loc[self._tickers, self._columns] = getter.legacy_dividends(self._tickers).transpose()
        df.loc[PORTFOLIO, self._columns] = df.multiply(self._amount, axis='index').sum(axis=0)
        return df

    def nominal_pretax_yields(self):
        """Номинальная дивидендная доходность"""
        nominal_dividends = self.nominal_pretax_dividends()
        inverse_prices = 1 / self._df[PRICE]
        return nominal_dividends.multiply(inverse_prices, axis='index')

    def dividends_yield(self):
        """Дивидендная доходность после уплаты налогов в реальном выражении (в ценах последнего года)"""
        cum_cpi = getter.cpi().cumprod()
        years = [pd.to_datetime(f'{year}-12-31') for year in self._columns]
        last_year_cpi_values = (cum_cpi[years[-1]] / cum_cpi[years]).values
        nominal_pretax_yields = self.nominal_pretax_yields()
        real_pretax_yields = nominal_pretax_yields.multiply(last_year_cpi_values, axis='columns')
        return real_pretax_yields * AFTER_TAX

    def m_dividends_yield(self):
        """Матожидание дивидендной доходности"""
        return self.dividends_yield().mean(axis='columns', skipna=False)

    def s_dividends_yield(self):
        """СКО дивидендной доходности

        СКО портфеля рассчитывается из допущения нулевой корреляции между дивидендами отдельных позиций - можно вывести
        аналитическую формулу. Допущение о нулевой корреляции необходимо в качестве простого приема
        регуляризации, так как число лет существенно меньше количества позиции. Данное допущение используется во всех
        дальнейших расчетах
        """
        std = self.dividends_yield().std(axis='columns', ddof=1, skipna=False)
        weighted_std = std.loc[self._tickers] * self._df.loc[self._tickers, WEIGHT]
        std[PORTFOLIO] = (weighted_std ** 2).sum(axis='index') ** 0.5
        return std


if __name__ == '__main__':
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123))
    dividends = DividendsMetrics(port, 2012, 2016)
    print(dividends.s_dividends_yield())
