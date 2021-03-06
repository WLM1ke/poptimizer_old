"""Генерация кейсов для обучения и валидации моделей"""
import catboost
import numpy as np
import pandas as pd

import local
from local import moex, dividends
from local.dividends.sqlite import STATISTICS_START
from settings import AFTER_TAX
from utils.aggregation import Freq
from web.labels import TICKER

MONTH_IN_YEAR = 12


class DividendsCasesIterator:
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
        self._prices = moex.prices(tickers).fillna(method='ffill', axis='index')

    def __iter__(self):
        date = pd.Timestamp(STATISTICS_START) + pd.DateOffset(years=self._years + 1)
        end_of_period_offset = self._freq.aggregation_func(self._last_date)
        date = end_of_period_offset(date)
        while date <= self._last_date:
            yield self.cases(date)
            date = end_of_period_offset(date + pd.DateOffset(days=1))

    def _real_dividends_yields(self, date: pd.Timestamp, labels: bool = True):
        """Возвращает посленалоговые дивидендные доходности в постоянных ценах для заданной даты

        Parameters
        ----------
        date
            Дата для которой, рассчитываются кейсы
        labels
            Если True, то информация создается для lags_range + 1 лет - последний год прогнозный

        Returns
        -------
        pd.DataFrame
            Кейс с частотой freq
        """
        if labels:
            months_in_period = MONTH_IN_YEAR * (self._years + 1)
            base_index = - MONTH_IN_YEAR - 1
        else:
            months_in_period = MONTH_IN_YEAR * self._years
            base_index = - 1
        cpi_index = self._cpi_index(date, months_in_period, base_index)
        agg_dividends = self._aggregated_real_after_tax_dividends(date, months_in_period, cpi_index)
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

    def _aggregated_real_after_tax_dividends(self, date, months, cpi_index):
        """Дивиденды за определенное число months до date агрегированные до нужной частоты и переведенные"""
        pre_tax_dividends = dividends.monthly_dividends(self._tickers, date).iloc[-months:, :]
        after_tax_dividends = pre_tax_dividends * AFTER_TAX
        real_after_tax_dividends = after_tax_dividends.mul(cpi_index, axis='index')
        agg_dividends = real_after_tax_dividends.groupby(by=self._freq.aggregation_func(date)).sum()
        return agg_dividends

    def cases(self, date: pd.Timestamp, predicted: bool = True):
        """Возвращает кейсы для заданной даты и частоты в формате DataFrame

        Первый столбец содержит тикер, далее столбцы с дивидендной доходность необходимой частоты за lag лет, а в
        последнем столбце годовая доходность в прогнозном году
        """
        cases = self._real_dividends_yields(date, predicted)
        if predicted:
            y = cases.iloc[:, -self._freq.times_in_year:].sum(axis='columns')
            cases.drop(columns=cases.columns[-self._freq.times_in_year:], inplace=True)
            cases['y'] = y
        else:
            cases['y'] = np.nan
        cases.columns = [TICKER] + [f'lag - {i}' for i in range(self._years * self._freq.times_in_year, 0, -1)] + ['y']
        return cases


def learn_pool_params(tickers, last_date, freq, lags):
    """Параметры для создания catboost.Pool для обучения"""
    learn_cases = pd.concat(DividendsCasesIterator(tickers, last_date, freq, lags))
    pool_params = dict(data=learn_cases.iloc[:, :-1],
                       label=learn_cases.iloc[:, -1],
                       cat_features=[0],
                       feature_names=learn_cases.columns[:-1])
    return pool_params


def learn_pool(tickers: tuple, last_date: pd.Timestamp, freq: Freq, lags: int = 5):
    """Возвращает обучающие кейсы до указанной даты включительно в формате Pool

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
    catboost.Pool
        Кейсы для обучения
    """
    pool_params = learn_pool_params(tickers, last_date, freq, lags)
    return catboost.Pool(**pool_params)


def predict_pool(tickers: tuple, last_date: pd.Timestamp, freq: Freq, lags: int = 5):
    """Возвращает кейсы предсказания до указанной даты включительно в формате Pool

    Кейсы состоят из значений дивидендной доходности за последние years лет с частотой freq за период с начала
    данных до last_date

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
    catboost.Pool
        Кейсы для предсказания
    """
    predict_cases = DividendsCasesIterator(tickers, last_date, freq, lags).cases(last_date, predicted=False)
    predict = catboost.Pool(data=predict_cases.iloc[:, :-1],
                            label=None,
                            cat_features=[0],
                            feature_names=predict_cases.columns[:-1])
    return predict


if __name__ == '__main__':
    POSITIONS = dict(AKRN=563,
                     BANEP=488,
                     CHMF=234)
    it = learn_pool(tuple(key for key in POSITIONS), pd.Timestamp('2018-08-17'), Freq.yearly, 4)
    print(it.get_features())
