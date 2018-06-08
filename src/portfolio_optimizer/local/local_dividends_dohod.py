"""Сохраняет, обновляет и загружает локальную версию данных по дивидендам с dohod.ru"""

import arrow

from portfolio_optimizer import web
from portfolio_optimizer.local.data_manager import DataManager
from portfolio_optimizer.web.labels import DATE

DIVIDENDS_CATEGORY = 'dividends_dohod'
DAYS_TO_UPDATE = 7


class DividendsDataManager(DataManager):
    """Реализует особенность загрузки истории дивидендов с обновлением раз в неделю

    Несколько платежей в одну дату суммируются
    """

    def __init__(self, ticker: str):
        def web_dividends_function_with_aggregation():
            return web.dividends_dohod(ticker).groupby(DATE).sum()

        super().__init__(DIVIDENDS_CATEGORY, ticker, web_dividends_function_with_aggregation)

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
