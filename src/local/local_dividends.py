"""Загружает локальную версию данных по дивидендам и обновляет после ручной проверки"""

import sqlite3

import arrow
import numpy as np
import pandas as pd

from local import local_dividends_dohod, local_dividends_smart_lab
from local.data_file import DataFile
from settings import DATA_PATH
from web.labels import DATE, TICKER, DIVIDENDS

DIVIDENDS_CATEGORY = 'dividends'
DIVIDENDS_SOURCES = [local_dividends_dohod.dividends_dohod,
                     local_dividends_smart_lab.dividends_smart_lab]
DAYS_TO_MANUAL_UPDATE = 90
STATISTICS_START = '2010-01-01'
DATABASE = str(DATA_PATH / DIVIDENDS_CATEGORY / 'dividends.db')


class DividendsDataManager:
    """Загружает локальную версию дивидендов и проверяет наличие данных во внешних источниках"""

    def __init__(self, ticker: str):
        self._ticker = ticker
        self._file = DataFile(DIVIDENDS_CATEGORY, ticker)

    def need_update(self):
        """Проверяет необходимость обновления данных

        Обновление нужно:
        при отсутствии локальных данных
        при наличии новых данных в локальной версии web источника
        по прошествии времени (дивиденды не выплачиваются чаще чем раз в квартал)
        """
        last_update = self._file.last_update()
        if last_update is None:
            return 'Нет локальных данных'
        if last_update.shift(days=DAYS_TO_MANUAL_UPDATE) < arrow.now():
            return f'Последнее обновление более {DAYS_TO_MANUAL_UPDATE} дней назад'
        for source in DIVIDENDS_SOURCES:
            df = self.get()
            local_web_df = source(self._ticker).groupby(DATE).sum()
            local_web_df = local_web_df[local_web_df.index >= pd.Timestamp(STATISTICS_START)]
            additional_data = local_web_df.index.difference(df.index)
            if not additional_data.empty:
                return f'В источнике {source.__module__} присутствуют дополнительные данные {additional_data}'
            df = df[local_web_df.index]
            if not np.allclose(df, local_web_df):
                return f'В источнике {source.__module__} не совпадают данные'
        return 'OK'

    def update(self):
        """Обновляет локальную версию данных на основании данных из базы

        Несколько платежей в одну дату объединяются
        Берется 0 колонка с дивидендами и отбрасывается с комментариями
        """
        connection = sqlite3.connect(DATABASE)
        query = f'SELECT * FROM {self._ticker}'
        df = pd.read_sql_query(query, connection, index_col=DATE, parse_dates=[DATE])
        df = df[df.index >= pd.Timestamp(STATISTICS_START)]
        df = df.groupby(DATE).sum()
        df.sort_index(inplace=True)
        df.columns = [self._ticker]
        self._file.dump(df[self._ticker])

    def get(self):
        """Получение данных"""
        return self._file.load()


def monthly_dividends(tickers: tuple, last_date: pd.Timestamp):
    """Возвращает ряды данных по месячным дивидендам для кортежа тикеров

    Parameters
    ----------
    tickers
        Кортеж тикеров, для которого нужно предоставить данные
    last_date
        Конечная дата в ряде данных. Ее день месяца используется для разбиения данных по месяцам

    Returns
    -------
    pd.DataFrame
        Столбцы - отдельные тикеры
        Строки - последние даты месяца
    """
    frames = (DividendsDataManager(ticker).get() for ticker in tickers)
    df = pd.concat(frames, axis='columns')
    month_end_day = last_date.day
    start_date = pd.Timestamp(STATISTICS_START) + pd.DateOffset(day=month_end_day) + pd.DateOffset(days=1)
    index = pd.DatetimeIndex(start=start_date, end=last_date, freq='D')
    df = df.reindex(index=index)

    def monthly_aggregation(x: pd.Timestamp):
        if x.day <= month_end_day:
            return x + pd.DateOffset(day=month_end_day)
        else:
            return x + pd.DateOffset(months=1, day=month_end_day)

    return df.groupby(by=monthly_aggregation).sum()


def smart_lab_status(tickers: tuple):
    """Информация об актуальности данных в основной локальной базе дивидендов

    Parameters
    ----------
    tickers
        Основные тикеры, для которых нужно проверить актуальность данных

    Returns
    -------
    tuple of list
        Нулевой элемент кортежа - список тикеров из переданных без актуальной информации в локальной базе
        Первый элемент кортежа - список тикеров со СмартЛаба, по которым нет актуальной информации в локальной базе
    """
    df = local_dividends_smart_lab.dividends_smart_lab()
    result = ([], [])
    for i in range(len(df)):
        date = df.index[i]
        ticker = df.iloc[i][TICKER]
        value = df.iloc[i][DIVIDENDS]
        local_data = DividendsDataManager(ticker).get()
        if (local_data is None) or (date not in local_data.index) or (local_data[date] != value):
            if ticker in tickers:
                result[0].append(ticker)
            else:
                result[1].append(ticker)
    return result


if __name__ == '__main__':
    name = 'MTSS'
    manager = DividendsDataManager(name)
    print('Статус данных -', manager.need_update())
    manager.update()
    print('Статус данных -', manager.need_update())
    print(smart_lab_status(('CHMF',)))
