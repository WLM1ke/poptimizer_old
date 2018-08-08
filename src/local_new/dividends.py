"""Реализация менеджера данных для дивидендов и вспомогательные функции"""

import sqlite3

import pandas as pd

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
        """Обновляет локальную версию данных на основании данных из базы базы данных

        Несколько платежей в одну дату объединяются
        Берется 0 колонка с дивидендами и отбрасывается с комментариями
        """
        connection = sqlite3.connect(DATABASE)
        query = f'SELECT * FROM {self.data_name}'
        df = pd.read_sql_query(query, connection, index_col=DATE, parse_dates=[DATE])
        df = df[df.index >= pd.Timestamp(STATISTICS_START)]
        # Несколько выплат в одну дату объединяются
        df = df.groupby(DATE).sum()
        df.columns = [self.data_name]
        return df

    def download_update(self):
        super().download_update()


if __name__ == '__main__':
    print(DividendsDataManager('AKRN'))
