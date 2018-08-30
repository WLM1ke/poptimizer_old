"""Генерация кейсов для обучения и валидации моделей"""
from enum import Enum

import catboost
import pandas as pd

import local
from local.local_dividends import STATISTICS_START
from settings import AFTER_TAX
from utils import aggregation
from web.labels import TICKER

MONTH_IN_YEAR = 12


class Freq(Enum):
    """Различные периоды агригации данных для построения обучающих кейсов"""
    monthly = (aggregation.monthly_aggregation_func, 12)
    quarterly = (aggregation.quarterly_aggregation_func, 4)
    yearly = (aggregation.yearly_aggregation_func, 1)

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
            yield self.cases(date)
            date = end_of_period_offset(date + pd.DateOffset(days=1))

    def _real_dividends_yields(self, date: pd.Timestamp, predicted: bool = True):
        """Возвращает посленалоговые дивидендные доходности в постоянных ценах для заданной даты

        Parameters
        ----------
        date
            Дата для которой, рассчитываются кейсы
        predicted
            Если True, то информация создается для lags + 1 лет - последний год прогнозный

        Returns
        -------
        pd.DataFrame
            Кейс с частотой freq
        """
        if predicted:
            months_in_period = MONTH_IN_YEAR * (self._years + 1)
            base_index = - MONTH_IN_YEAR - 1
        else:
            months_in_period = MONTH_IN_YEAR * self._years
            base_index = - 1
        cpi_index = self._cpi_index(date, months_in_period, base_index)
        agg_dividends = self._aggregated_real_after_tax_dividends(self._tickers, date, months_in_period, cpi_index)
        base_date = cpi_index.index[base_index]
        price = self._prices.reindex(index=[base_date], method='ffill').iloc[0]
        yields = agg_dividends.div(price, axis='columns')
        yields = yields.T
        yields.dropna(inplace=True)
        yields.reset_index(TICKER, inplace=True)
        return yields

    @staticmethod
    def _cpi_index(date, months, base_index):
        """Индекс цен за определенное число months до date и приведенная к месяцу с номером base_index"""
        cum_cpi = local.monthly_cpi(date).iloc[-months:].cumprod()
        cpi_index = cum_cpi.iat[base_index] / cum_cpi
        return cpi_index

    def _aggregated_real_after_tax_dividends(self, tickers, date, months, cpi_index):
        """Дивиденды за определенное число months до date агрегированные до нужной частоты и переведенные"""
        dividends = local.monthly_dividends(tickers, date).iloc[-months:, :]
        after_tax_dividends = dividends * AFTER_TAX
        real_after_tax_dividends = after_tax_dividends.mul(cpi_index, axis='index')
        agg_dividends = real_after_tax_dividends.groupby(by=self._freq.aggregation_func(date)).sum()
        return agg_dividends

    def cases(self, date: pd.Timestamp, predicted: bool = True):
        """Возвращает кейсы для заданной даты и частоты"""
        cases = self._real_dividends_yields(date, predicted)
        if predicted:
            y = cases.iloc[:, -self._freq.times_in_year:].sum(axis='columns')
            cases.drop(columns=cases.columns[-self._freq.times_in_year:], inplace=True)
            cases['y'] = y
        else:
            cases['y'] = None
        cases.columns = [TICKER] + [f'lag - {i}' for i in range(self._years * self._freq.times_in_year, 0, -1)] + ['y']
        return cases


def learn_predict_pools(tickers: tuple, last_date: pd.Timestamp, freq: Freq, lags: int = 5):
    """Возвращает обучающие кейсы до указанной даты включительно и данные для прогнозирования в формате Pool

    Кейсы состоят из значений дивидендной доходности за последние years лет с частотой freq за период с начала данных до
    last_date

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
    tuple
        Первый элемент кортежа кейсы для обучения в формате Pool
        Второй элемент кортежа кейсы для прогнозирования в формате Pool
    """
    learn_cases = pd.concat(RawCasesIterator(tickers, last_date, freq, lags))
    learn = catboost.Pool(data=learn_cases.iloc[:, :-1],
                          label=learn_cases.iloc[:, -1],
                          cat_features=[0],
                          feature_names=learn_cases.columns[:-1])
    predict_cases = RawCasesIterator(tickers, last_date, freq, lags).cases(last_date, predicted=False)
    predict = catboost.Pool(data=predict_cases.iloc[:, :-1],
                            label=None,
                            cat_features=[0],
                            feature_names=predict_cases.columns[:-1])
    return learn, predict


if __name__ == '__main__':
    POSITIONS = dict(AKRN=563,
                     BANEP=488,
                     CHMF=234)
    it = learn_predict_pools(tuple(key for key in POSITIONS), pd.Timestamp('2018-08-17'), Freq.yearly, 4)
    print(it[0].shape)
