"""Генерация кейсов для обучения и валидации моделей"""
import functools

import pandas as pd

import local
from local.local_dividends import STATISTICS_START
from settings import AFTER_TAX
from web.labels import DATE, TICKER


def real_after_tax_yearly_dividends(cum_cpi, last_date, tickers):
    dividends = local.monthly_dividends(tickers, last_date)
    after_tax_dividends = dividends * AFTER_TAX
    real_after_tax_dividends = after_tax_dividends.div(cum_cpi, axis='index')
    aggregation_func = functools.partial(yearly_aggregation, end_of_year=last_date)
    return real_after_tax_dividends.groupby(by=aggregation_func).sum()


def yearly_aggregation(x: pd.Timestamp, end_of_year: pd.Timestamp):
    end_month = end_of_year.month
    end_day = end_of_year.day
    if (x.month, x.day) <= (end_month, end_day):
        return x + pd.DateOffset(month=end_month, day=end_day)
    else:
        return x + pd.DateOffset(years=1, month=end_month, day=end_day)


def real_yearly_price(tickers, start_date, cum_cpi):
    prices = local.prices(tickers)[start_date:]
    prices = prices.reindex(cum_cpi.index, method='ffill')
    real_price = prices.div(cum_cpi, axis='index')
    return real_price


def real_prices_dividends(last_date, tickers):
    start_date = pd.Timestamp(STATISTICS_START) + pd.DateOffset(day=last_date.day) + pd.DateOffset(days=1)
    cpi = local.cpi_to_date(last_date)[start_date:]
    cum_cpi = cpi.cumprod()
    real_after_tax_dividends = real_after_tax_yearly_dividends(cum_cpi, last_date, tickers)
    cum_cpi = cum_cpi.reindex(real_after_tax_dividends.index)
    real_price = real_yearly_price(tickers, start_date, cum_cpi)
    return real_after_tax_dividends, real_price


def ticker_cases(dividends, price, lags):
    ticker = price.name
    dividends = dividends.to_frame()
    dividends[TICKER] = ticker
    for lag in range(lags + 1):
        dividends[f'lag - {lag}'] = dividends[ticker].shift(lag) / price
    dividends.dropna(inplace=True)
    dividends.drop(columns=ticker, inplace=True)
    dividends.index.name = DATE
    dividends.reset_index(inplace=True)
    return dividends


def yield_cases(lags, last_date, tickers):
    real_after_tax_dividends, real_price = real_prices_dividends(last_date, tickers)
    for ticker in tickers:
        dividends = real_after_tax_dividends[ticker]
        price = real_price[ticker]
        yield ticker_cases(dividends, price, lags)


def cases(tickers: tuple, last_date: pd.Timestamp, lags=5):
    return pd.concat(yield_cases(lags, last_date, tickers), axis='index', ignore_index=True)


if __name__ == '__main__':
    POSITIONS = dict(AKRN=563,
                     BANEP=488,
                     CHMF=234,
                     GMKN=146,
                     LKOH=340,
                     LSNGP=18,
                     LSRG=2346,
                     MSRS=128,
                     MSTT=1823,
                     MTSS=1302,
                     PMSBP=2796,
                     RTKMP=1726,
                     SNGSP=318,
                     TTLK=234,
                     UPRO=986,
                     VSMO=102,
                     PRTK=0,
                     MVID=0,
                     ALRS=0)
    cc = cases(tuple(key for key in POSITIONS), pd.Timestamp('2018-08-10'))
    print(cc)
    from sklearn.model_selection import LeaveOneGroupOut

    x = cc[[DATE, TICKER] + [f'lag - {lag}' for lag in range(1, 6)]]
    y = cc['lag - 0']
    groups = cc[TICKER]
    print(len(list(LeaveOneGroupOut().split(x, y, groups))))
