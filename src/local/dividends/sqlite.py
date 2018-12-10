"""Реализация менеджера данных для дивидендов и вспомогательные функции"""
import functools
import sqlite3

import pandas as pd
from pandas.io.sql import DatabaseError

from settings import DATA_PATH
from utils.aggregation import monthly_aggregation_func
from utils.data_manager import AbstractDataManager
from web.labels import DATE
from web.labels import TICKER

DIVIDENDS_CATEGORY = 'dividends'
STATISTICS_START = '2010-01-01'
DATABASE = str(DATA_PATH / '../../poptimizer/data/dividends.db')


class DividendsDataManager(AbstractDataManager):
    """Организация создания, обновления и предоставления локальных DataFrame

    Данные загружаются из локальной базы данных и сохраняются в общем формате DataManager
    """
    def __init__(self, ticker: str):
        super().__init__(DIVIDENDS_CATEGORY, ticker)

    def download_all(self):
        """Загружает данные из базы базы данных

        Несколько платежей в одну дату объединяются
        Берется колонка с дивидендами и отбрасывается с комментариями
        В случае отсутствия данных возвращается пустая Series
        """
        connection = sqlite3.connect(DATABASE)
        query = f'SELECT DATE, DIVIDENDS FROM {self.data_name}'
        try:
            df = pd.read_sql_query(query, connection, index_col=DATE, parse_dates=[DATE])
        except DatabaseError:
            return pd.Series(name=self.data_name, index=pd.DatetimeIndex([], name=DATE))
        else:
            df = df[df.index >= pd.Timestamp(STATISTICS_START)]
            # Несколько выплат в одну дату объединяются
            df = df.groupby(DATE).sum()
            df.columns = [self.data_name]
            return df[self.data_name]

    def download_update(self):
        super().download_update()


@functools.lru_cache(maxsize=1)
def tickers_dividends(tickers: tuple):
    """Сводная информация по дивидендам для заданных тикеров"""
    frames = (DividendsDataManager(ticker).value for ticker in tickers)
    df = pd.concat(frames, axis='columns')
    df.columns.name = TICKER
    return df


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
    df = tickers_dividends(tickers)
    month_end_day = last_date.day
    crop_date = pd.Timestamp(STATISTICS_START) + pd.DateOffset(day=month_end_day, days=1)
    df = df.loc[crop_date:, :]
    df = df.groupby(by=monthly_aggregation_func(last_date)).sum()
    start_date = pd.Timestamp(STATISTICS_START) + pd.DateOffset(months=1, day=month_end_day)
    offset = pd.DateOffset(months=1, day=month_end_day)
    index = pd.DatetimeIndex(start=start_date, end=last_date, freq=offset)
    df = df.reindex(index=index, fill_value=0)
    return df


if __name__ == '__main__':
    df_ = monthly_dividends(tuple(['AKRN']), pd.Timestamp('2018-12-07'))
    print(df_)
