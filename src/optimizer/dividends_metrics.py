"""Реализация основных метрик дивидендного потока"""

import pandas as pd

from optimizer import getter
from optimizer.portfolio import Portfolio
from optimizer.settings import LOTS, LOT_SIZE, PORTFOLIO, AFTER_TAX, PRICE


class DividendsMetrics:
    """Реализует основные метрики дивидендного потока для портфеля

    За основу берутся legacy nominal_retax_dividends для интервала лет с first_year до last_year включительно
    """

    def __init__(self, portfolio: Portfolio, first_year: int, last_year: int):
        self._portfolio = portfolio
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
        inverse_prices = 1 / self._portfolio.df[PRICE]
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
        pass



if __name__ == '__main__':
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123))
    dividends = DividendsMetrics(port, 2012, 2016)
    print(dividends.dividends_yield())
