"""Сохраняет, обновляет и загружает локальную версию данных по дивидендам с dohod.ru"""

import arrow

import web
from local.data_manager import DataManager
from web.labels import DATE

DIVIDENDS_CATEGORY = 'dividends_dohod'
DAYS_TO_UPDATE = 7


class DividendsDohodDataManager(DataManager):
    """Реализует особенность загрузки истории дивидендов с обновлением раз в неделю

    Несколько платежей в одну дату суммируются
    """
    days_to_update = DAYS_TO_UPDATE

    def __init__(self, ticker: str):

        def web_dividends_function_with_aggregation():
            """Web-данные содержат по несколько выплат на одну дату

            Для прохождения валидации и последующих сопоставлений необходима агрегация
            """
            return web.dividends_dohod(ticker).groupby(DATE).sum()

        super().__init__(DIVIDENDS_CATEGORY, ticker, web_dividends_function_with_aggregation)

    def _need_update(self):
        """Обновление осуществляется через DAYS_TO_UPDATE дней после предыдущего"""
        if self.file.last_update().shift(days=self.days_to_update) < arrow.now():
            return True
        return False


def dividends_dohod(ticker: str):
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
    data = DividendsDohodDataManager(ticker)
    return data.get()


if __name__ == '__main__':
    print(dividends_dohod('MFON'))
