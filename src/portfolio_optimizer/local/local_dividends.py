"""Загружает локальную версию данных по дивидендам и обновляет после ручной проверки"""

import sqlite3

import arrow
import pandas as pd

from portfolio_optimizer.local import local_dividends_dohod
from portfolio_optimizer.local.data_file import DataFile
from portfolio_optimizer.settings import DATA_PATH
from portfolio_optimizer.web.labels import DATE

DIVIDENDS_CATEGORY = 'dividends'
DIVIDENDS_SOURCES = [local_dividends_dohod.dividends]
DAYS_TO_MANUAL_UPDATE = 90
STATISTICS_START = '2010-01-01'
DATABASE = str(DATA_PATH / DIVIDENDS_CATEGORY / 'dividends.db')


class DividendsDataManager:
    """Загружает локальную версию дивидендов и проверяет наличие данных во внешних источниках"""

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.file = DataFile(DIVIDENDS_CATEGORY, ticker)

    def need_update(self):
        """Проверяет необходимость обновления данных

        Обновление нужно:
        при отсутствии локальных данных
        при наличии новых данных в локальной версии web источника
        по прошествии времени (дивиденды не выплачиваются чаще чем раз в квартал)
        """
        last_update = self.file.last_update()
        if last_update is None:
            return 'Нет локальных данных'
        if last_update.shift(days=DAYS_TO_MANUAL_UPDATE) < arrow.now():
            return f'Последнее обновление более {DAYS_TO_MANUAL_UPDATE} дней назад'
        for source in DIVIDENDS_SOURCES:
            df = self.get()
            local_web_df = source(self.ticker).groupby(DATE).sum()
            local_web_df = local_web_df[local_web_df.index >= pd.Timestamp(STATISTICS_START)]
            if not local_web_df.index.difference(df.index).empty:
                return f'В источнике {source.__name__} присутствуют дополнительные данные'
            df = df[local_web_df.index]
            if not df.equals(local_web_df):
                return f'В источнике {source.__name__} не совпадают данные'
        return 'OK'

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

    def get_raw(self):
        """Получение данных - несколько платежей в одну дату не объединяются"""
        return self.file.load()

    def get(self):
        """Получение данных - несколько платежей в одну дату объединяются"""
        return self.file.load().groupby(DATE).sum()


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


def dividends_update_status(tickers: tuple):
    """Возвращает статус обновления данных по дивидендам


    Parameters
    ----------
    tickers
        Кортеж тикеров, для которых нужно предоставить данные

    Returns
    -------
    list of str or None
        Возвращает список, который содержит строки с текстовыми сообщениями о причинах неактуальности данных для тикера
    """
    return [DividendsDataManager(ticker).need_update() for ticker in tickers]


if __name__ == '__main__':
    name = 'GMKN'
    manager = DividendsDataManager(name)
    print('Статус данных -', manager.need_update())
    print(manager.get_raw())
    manager.update()
    print('Статус данных -', manager.need_update())
    print(manager.get_raw())
