"""Сохраняет, обновляет и загружает локальную версию данных по дивидендам"""

import functools

from portfolio_optimizer import web
from portfolio_optimizer.local.data_manager import DataManager

DIVIDENDS_CATEGORY = 'dividends_old'


class DividendsDataManager(DataManager):
    """Реализует особенность загрузки истории дивидендов"""

    def __init__(self, ticker: str):
        web_dividends_function = functools.partial(web.dividends, ticker=ticker)
        super().__init__(DIVIDENDS_CATEGORY, ticker, web_dividends_function)


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
    data = DividendsDataManager(ticker)
    return data.get()


if __name__ == '__main__':
    print(dividends('GAZP'))
