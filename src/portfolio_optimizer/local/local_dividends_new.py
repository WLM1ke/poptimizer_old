"""Загружает локальную версию данных по дивидендам и обновляет после ручной проверки"""

import arrow
import pandas as pd

from portfolio_optimizer import web
from portfolio_optimizer.local.data_file import DataFile
from portfolio_optimizer.web.labels import DATE

DIVIDENDS_CATEGORY = 'dividends'
DIVIDENDS_SOURCES = [web.dividends]
DAYS_TO_WEB_UPDATE = 7
DAYS_TO_MANUAL_UPDATE = 90


class DividendsDataManager:
    """Загружает локальную версию дивидендов и проверяет наличие данных во внешних источниках"""

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.file = DataFile(DIVIDENDS_CATEGORY, ticker)

    def _need_update(self):
        """Проверяет необходимость обновления данных

        Обновление нужно:
        при отсутствии локальных данных
        при наличии новых  данных в web источнике (проверка раз в неделю)
        по прошествии времени (дивиденды не выплачиваются чаще чем раз в квартал
        """
        last_update = self.file.last_update()
        if last_update is None:
            return True
        if last_update.shift(days=DAYS_TO_MANUAL_UPDATE) < arrow.now():
            return True
        if last_update.shift(days=DAYS_TO_WEB_UPDATE) < arrow.now():
            for source in DIVIDENDS_SOURCES:
                local_df = self.file.load()
                web_df = source(self.ticker)
                web_df = web_df[web_df.index >= local_df.index[0]]
                if not web_df.index.difference(local_df.index).empty:
                    return True
        return False

    def update(self, data: list):
        """Добавляет данные по дивидендам в локальную версию данных

        Parameters
        ----------
        data
            Список из списков [дата, дивиденды]
        """
        df = self.file.load()
        if df is None:
            df = pd.Series(name=self.ticker)
            df.index.name = DATE
        new_df = pd.Series(name=self.ticker,
                           index=[pd.Timestamp(i[0]) for i in data],
                           data=[i[1] for i in data])
        df = df.append(new_df)
        df.sort_index(inplace=True)
        self.file.dump(df)

    def get(self):
        """Получение данных и статуса необходимости обновления"""
        return self.file.load(), self._need_update()


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
    name = 'AKRN'
    print(dividends(name))
    data_manager = DividendsDataManager(name)
    """data_manager.update([['2010-04-09', 25],
                         ['2011-04-08', 40],
                         ['2011-09-01', 129],
                         ['2012-11-12', 46],
                         ['2013-04-11', 110 - 46],
                         ['2014-06-09', 152],
                         ['2015-06-02', 139],
                         ['2016-06-14', 180],
                         ['2016-09-20', 155],
                         ['2017-07-11', 250 - 155],
                         ['2017-09-26', 235],
                         ['2018-01-23', 112],
                         ['2018-06-14', 185]])"""
    print(dividends(name))

    # TODO: удалить старую реализацию и тесты к ней
