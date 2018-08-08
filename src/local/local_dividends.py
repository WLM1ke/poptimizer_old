"""Реализация менеджера данных для дивидендов и вспомогательные функции"""

import sqlite3

import pandas as pd
from pandas.io.sql import DatabaseError

from local_new.data_manager import AbstractDataManager
from settings import DATA_PATH
from web.labels import DATE

DIVIDENDS_CATEGORY = 'dividends'
STATISTICS_START = '2010-01-01'
DATABASE = DATA_PATH / 'dividends.db'


class DividendsDataManager(AbstractDataManager):
    """Организация создания, обновления и предоставления локальных DataFrame

    Данные загружаются из локальной базы данных и сохраняются в общем формате DataManager
    """

    def __init__(self, ticker: str):
        super().__init__(DIVIDENDS_CATEGORY, ticker)

    def download_all(self):
        """Загружает данные из базы базы данных

        Несколько платежей в одну дату объединяются
        Берется 0 колонка с дивидендами и отбрасывается с комментариями
        """
        connection = sqlite3.connect(DATABASE)
        query = f'SELECT DATE, DIVIDENDS FROM {self.data_name}'
        try:
            df = pd.read_sql_query(query, connection, index_col=DATE, parse_dates=[DATE])
        except DatabaseError:
            raise ValueError(f'Дивиденды {self.data_name} отсутствуют в базе данных')
        else:
            df = df[df.index >= pd.Timestamp(STATISTICS_START)]
            # Несколько выплат в одну дату объединяются
            df = df.groupby(DATE).sum()
            df.columns = [self.data_name]
            return df[self.data_name]

    def download_update(self):
        super().download_update()


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
    frames = (DividendsDataManager(ticker).value for ticker in tickers)
    df = pd.concat(frames, axis='columns')
    month_end_day = last_date.day
    start_date = pd.Timestamp(STATISTICS_START) + pd.DateOffset(day=month_end_day) + pd.DateOffset(days=1)
    index = pd.DatetimeIndex(start=start_date, end=last_date, freq='D')
    df = df.reindex(index=index)

    def monthly_aggregation(x: pd.Timestamp):
        """Агрегация месячных данных - конец месяца соответствует дню месяца из аргумента"""
        if x.day <= month_end_day:
            return x + pd.DateOffset(day=month_end_day)
        else:
            return x + pd.DateOffset(months=1, day=month_end_day)

    return df.groupby(by=monthly_aggregation).sum()


if __name__ == '__main__':
    print(DividendsDataManager('RTKMP'))
