"""Сохраняет, обновляет и загружает локальную версию данных по дивидендам с dohod.ru"""

import functools

import arrow

from portfolio_optimizer import web
from portfolio_optimizer.local.data_manager import DataManager

DIVIDENDS_CATEGORY = 'dividends_dohod'
DAYS_TO_UPDATE = 7


class DividendsDataManager(DataManager):
    """Реализует особенность загрузки истории дивидендов с обновлением раз в неделю"""

    def __init__(self, ticker: str):
        web_dividends_function = functools.partial(web.dividends_dohod, ticker=ticker)
        super().__init__(DIVIDENDS_CATEGORY, ticker, web_dividends_function)

    def _need_update(self):
        """Обновление осуществляется через DAYS_TO_UPDATE дней после предыдущего"""
        if self.file.last_update().shift(days=DAYS_TO_UPDATE) < arrow.now():
            return True
        return False


def dividends(ticker: str):
    """Сохраняет, при необходимости обновляет и возвращает дивиденды для тикеров

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
