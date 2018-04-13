"""Сохраняет, обновляет и загружает локальную версию данных по дивидендам"""

import functools

from portfolio_optimizer import web
from portfolio_optimizer.local.data_manager import DataManager

DIVIDENDS_CATEGORY = 'dividends'


def dividends(ticker: str):
    """
    Сохраняет, при необходимости обновляет и возвращает дивиденды для тикеров

    Parameters
    ----------
    ticker
        Список тикеров

    Returns
    -------
    pd.Series
        В строках - даты выплаты дивидендов
        Значения - выплаченные дивиденды
    """
    web_dividends_function = functools.partial(web.dividends, ticker=ticker)
    data = DataManager(DIVIDENDS_CATEGORY, ticker, web_dividends_function)
    return data.get()


if __name__ == '__main__':
    print(dividends('CHMF'))
