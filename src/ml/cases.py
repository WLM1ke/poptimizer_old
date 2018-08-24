"""Генерация кейсов для обучения и валидации моделей"""
from collections import namedtuple
from enum import Enum

import pandas as pd
from sklearn.preprocessing import OneHotEncoder

import local
from local.local_dividends import STATISTICS_START
from settings import AFTER_TAX
from utils.aggregation import yearly_aggregation_func, quarterly_aggregation_func, monthly_aggregation_func
from web.labels import DATE

MONTH_IN_YEAR = 12


class Freq(Enum):
    """Различные периоды агригации данных для построения обучающих кейсов"""
    monthly = (monthly_aggregation_func, 12)
    quarterly = (quarterly_aggregation_func, 4)
    yearly = (yearly_aggregation_func, 1)

    def __init__(self, aggregation_func, times_in_year):
        self._aggregation_func = aggregation_func
        self._times_in_year = times_in_year

    @property
    def aggregation_func(self):
        """Функция агригации"""
        return self._aggregation_func

    @property
    def times_in_year(self):
        """Количество периодов в году"""
        return self._times_in_year


class RawCasesIterator:
    """Итератор кейсов для обучения

    Кейсы состоят из значений дивидендной доходности за последние years лет с частотой freq и следующих годовых
    дивидендов за период с начала данных до last_date
    """

    def __init__(self, tickers: tuple, last_date: pd.Timestamp, freq: Freq, years: int = 5):
        self._tickers = tickers
        self._last_date = last_date
        self._freq = freq
        self._years = years
        # Дорогая операция - вызывается один раз при создании итератора для ускорения
        self._prices = local.prices(tickers).fillna(method='ffill', axis='index')


    def __iter__(self):
        date = pd.Timestamp(STATISTICS_START) + pd.DateOffset(years=self._years + 1)
        end_of_period_offset = self._freq.aggregation_func(self._last_date)
        date = end_of_period_offset(date)
        while date <= self._last_date:
            yield self.raw_cases(date)
            date = end_of_period_offset(date + pd.DateOffset(days=1))

    def _real_dividends_yields(self, date: pd.Timestamp):
        """Возвращает посленалоговые дивидендные доходности в постоянных ценах для заданной даты

        Информация за lags + 1 лет с частотой freq. Базисом для постоянных цен и доходности является конец
        предпоследнего года
        """
        tickers = self._tickers
        months_in_period = MONTH_IN_YEAR * (self._years + 1)
        cum_cpi = local.monthly_cpi(date).iloc[-months_in_period:].cumprod()
        base_date = cum_cpi.index[-MONTH_IN_YEAR - 1]
        cpi_index = cum_cpi.at[base_date] / cum_cpi
        dividends = local.monthly_dividends(tickers, date).iloc[-months_in_period:, :]
        after_tax_dividends = dividends * AFTER_TAX
        real_after_tax_dividends = after_tax_dividends.mul(cpi_index, axis='index')
        agg_dividends = real_after_tax_dividends.groupby(by=self._freq.aggregation_func(date)).sum()
        price = self._prices.reindex(index=[base_date], method='ffill').iloc[0]
        yields = agg_dividends.div(price, axis='columns')
        yields = yields.T
        yields[DATE] = base_date
        yields.set_index(DATE, append=True, inplace=True)
        return yields.dropna()

    def raw_cases(self, date: pd.Timestamp):
        """Возвращает кейсы для заданной даты и частоты в формате Data"""
        yields = self._real_dividends_yields(date)
        if len(yields) != len(self._tickers):
            raise ValueError(f'Количество тикеров не равно количеству кейсов для {date}')
        y = yields.iloc[:, -self._freq.times_in_year:].sum(axis='columns')
        yields.drop(columns=yields.columns[-self._freq.times_in_year:], inplace=True)
        yields.columns = [f'lag - {i}' for i in range(self._years * self._freq.times_in_year, 0, -1)]
        yields['y'] = y
        return yields


Cases = namedtuple('Cases', 'x y groups')


def all_cases(tickers: tuple, last_date: pd.Timestamp, freq: Freq, lags: int = 5):
    """Возвращает обучающие кейсы до указанной даты включительно

    Кейсы состоят из значений дивидендной доходности за последние years лет с частотой freq за период с начала данных до
    last_date и OneHot кодировки тикеров

    Parameters
    ----------
    tickers
        Кортеж тикеров
    last_date
        Последняя дата, на которую нужно подготовить кейсы
    freq
        Частота агрегации данных по дивидендам
    lags
        Количество лет данных по дивидендам

    Returns
    -------
    Data
        Кейсы для обучения
    """
    data = pd.concat(RawCasesIterator(tickers, last_date, freq, lags))
    index = data.index
    one_hot = OneHotEncoder(sparse=False).fit_transform(index.labels[0].reshape(-1, 1))
    one_hot = pd.DataFrame(data=one_hot, index=index, columns=index.levels[0])
    data = pd.concat([one_hot, data], axis='columns')
    return Cases(x=data.iloc[:, 0:-1], y=data.iloc[:, -1], groups=None)

if __name__ == '__main__':
    POSITIONS = dict(AKRN=563,
                     BANEP=488,
                     CHMF=234)
    it = all_cases(tuple(key for key in POSITIONS), pd.Timestamp('2018-08-17'), Freq.yearly, 2)
    print(it.x)
