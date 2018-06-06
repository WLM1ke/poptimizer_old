"""Загружает локальную версию данных по дивидендам и обновляет после ручной проверки"""

import sqlite3
from collections import namedtuple

import arrow
import pandas as pd

from portfolio_optimizer import web
from portfolio_optimizer.local.data_file import DataFile
from portfolio_optimizer.settings import DATA_PATH
from portfolio_optimizer.web.labels import DATE

DIVIDENDS_CATEGORY = 'dividends'
DIVIDENDS_SOURCES = [web.dividends]
DAYS_TO_WEB_UPDATE = 7
DAYS_TO_MANUAL_UPDATE = 90
STATISTICS_START = '2010-01-01'
DATABASE = str(DATA_PATH / DIVIDENDS_CATEGORY / 'dividends.db')

Dividends = namedtuple('Dividends', 'data, need_update')


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
                web_df = web_df[web_df.index >= pd.Timestamp(STATISTICS_START)]
                if not web_df.index.difference(local_df.index).empty:
                    return True
        return False

    def update(self):
        """Обновляет локальную версию данных на основании данных из базы"""
        connection = sqlite3.connect(DATABASE)
        query = f'SELECT * FROM {self.ticker}'
        df = pd.read_sql_query(query, connection, index_col=DATE, parse_dates=[DATE])
        df = df[df.index >= pd.Timestamp(STATISTICS_START)]
        df.sort_index(inplace=True)
        df.columns = [self.ticker]
        df = df[self.ticker]
        self.file.dump(df)

    def get(self):
        """Получение данных и статуса необходимости обновления"""
        return Dividends(self.file.load(), self._need_update())


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
    manager = DividendsDataManager(name)
    manager.update()
    print(dividends(name))
