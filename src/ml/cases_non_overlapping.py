"""Генерация кейсов для обучения и валидации моделей - результаты кейсов для одной бумаги не пересекаются во времени """
from collections import namedtuple

import pandas as pd

import local
from local.local_dividends import STATISTICS_START
from settings import AFTER_TAX
from utils.aggregation import yearly_aggregation_func
from web.labels import DATE, TICKER


def real_after_tax_yearly_dividends(tickers, start_date, last_date, cum_cpi):
    """Возвращает годовые дивиденды в постоянных ценах"""
    dividends = local.monthly_dividends(tickers, last_date)[start_date:]
    after_tax_dividends = dividends * AFTER_TAX
    real_after_tax_dividends = after_tax_dividends.div(cum_cpi, axis='index')
    return real_after_tax_dividends.groupby(by=yearly_aggregation_func(end_of_year=last_date)).sum()


def real_yearly_price(tickers, start_date, cum_cpi):
    """Возвращает цены акций на конец каждого года в постоянных ценах"""
    prices = local.prices(tickers)[start_date:]
    prices = prices.reindex(cum_cpi.index, method='ffill')
    real_price = prices.div(cum_cpi, axis='index')
    return real_price


def real_prices_and_dividends(tickers, last_date):
    """Возвращает кортеж из цен акций в реальном выражении и годовых дивидендов в реальном выражении"""
    start_date = (pd.Timestamp(STATISTICS_START)
                  + pd.DateOffset(month=last_date.month, day=last_date.day)
                  + pd.DateOffset(days=1))
    cpi = local.monthly_cpi(last_date)[start_date:]
    cum_cpi = cpi.cumprod()
    real_after_tax_dividends = real_after_tax_yearly_dividends(tickers, start_date, last_date, cum_cpi)
    cum_cpi = cum_cpi.reindex(real_after_tax_dividends.index)
    real_prices = real_yearly_price(tickers, start_date, cum_cpi)
    return real_after_tax_dividends, real_prices


def ticker_cases(dividends, price, lags):
    """Формирует блок кейсов для одного тикера на основе реальных цен и дивидендов"""
    ticker = price.name
    cases = pd.DataFrame(ticker, columns=[TICKER], index=dividends.index)
    price = price.shift(1)
    for lag in range(lags + 1):
        cases[f'lag - {lag}'] = dividends.shift(lag) / price
    cases.index.name = DATE
    cases.reset_index(inplace=True)
    cases[DATE] = cases[DATE].shift(1)
    cases.dropna(inplace=True)
    return cases


def yield_cases(tickers, last_date, lags):
    """Генерирует блоки кейсов для отдельного тикера из списка тикеров"""
    real_after_tax_dividends, real_price = real_prices_and_dividends(tickers, last_date)
    for ticker in tickers:
        dividends = real_after_tax_dividends[ticker]
        price = real_price[ticker]
        yield ticker_cases(dividends, price, lags)


Data = namedtuple('Data', 'x y groups')


def cases_non_overlapping(tickers: tuple, last_date: pd.Timestamp, lags=5):
    """Возвращает DataFrame с кейсами для обучения

    Результаты кейсов для одного тикера не перекрываются во времени. Состоят из Timestamp начала нулевого периода,
    тикера и значения реальной годовой дивидендной доходности с несколькими лагами. Дивидендная доходность
    пересчитывается в постоянные цены на начало нулевого периода

    Parameters
    ----------
    tickers
        Кортеж тикеров, на основании которых нужно построить тестовые кейсы
    last_date
        Последняя дата, до которой нужно использовать статистику. Начальная дата статистики установлена в модуле,
        отвечающем за хранение локальной версии данных
    lags
        Сколько лагов значения реальных годовых дивидендов нужно добавить в обучающую выборку

    Returns
    -------
    DataFrame
        В строках - отдельные кейсы
        В столбцах - Timestamp и тикер кейса + значение реальных годовых дивидендов с заданным числом лагов
    """
    df = pd.concat(yield_cases(tickers, last_date, lags), axis='index', ignore_index=True)
    return Data(df.iloc[:, 3:], df.iloc[:, 2], df.iloc[:, 1])


if __name__ == '__main__':
    lags_ = 5
    cc = cases_non_overlapping(tuple(['GMKN', 'LSRG', 'MSTT']), pd.Timestamp('2017-05-21'), lags=lags_)
    print(cc.y)
