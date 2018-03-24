"""Load and update local data for dividends history and returns pandas DataFrames.

    get_dividends(tickers)
"""

import time
from os import path

import numpy as np
import pandas as pd

import optimizer.storage
from optimizer import download
from optimizer.settings import DATE, DIVIDENDS

DIVIDENDS_FOLDER = 'dividends'
UPDATE_PERIOD_IN_DAYS = 1


class LocalDividends:
    """Реализует хранение, обновление и хранение локальных данных по индексу дивидендам."""
    _data_folder = DIVIDENDS_FOLDER
    _load_converter = {DATE: pd.to_datetime, DIVIDENDS: pd.to_numeric}
    _data_columns = DIVIDENDS

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.df = None
        if self.local_data_path.exists():
            self.update_local_history()
        else:
            self.create_local_history()

    @property
    def local_data_path(self):
        """Возвращает и при необходимости создает путь к файлу с котировками."""
        return optimizer.storage.make_data_path(self._data_folder, f'{self.ticker}.csv')

    def _save_history(self):
        """Сохраняет локальную версию данных в csv-файл с именем тикера.

        Флаги заголовков необходимы для поддержки сохранения серий, а не только датафреймов."""
        self.df.to_csv(self.local_data_path, index=True, header=True)

    def load_local_history(self):
        """Загружает историю котировок из локальных данных.

        Значение sep гарантирует загрузку данных с добавленными PyCharm пробелами.
        """
        df = pd.read_csv(self.local_data_path,
                         converters=self._load_converter,
                         header=0,
                         engine='python',
                         sep='\s*,')
        self.df = df.set_index(DATE)
        return self.df[self._data_columns]

    def need_update(self):
        """Обновление требуется по прошествии фиксированного количества дней."""
        if time.time() - path.getmtime(self.local_data_path) > UPDATE_PERIOD_IN_DAYS * 60 * 60 * 24:
            return True
        return False

    def _validate_new_data(self, df_new):
        """Проверяем, что старые данные совпадают с новыми."""
        common_rows = list(set(self.df.index) & set(df_new.index))
        if not np.allclose(self.df.loc[common_rows], df_new.loc[common_rows]):
            raise ValueError(f'Новые данные по дивидендам {self.ticker} не совпадают с локальной версией.')

    def update_local_history(self):
        """Обновляет локальные данные данными из интернета и возвращает полную историю дивидендных выплат."""
        self.df = self.load_local_history()
        if self.need_update():
            df_update = download.dividends(self.ticker)
            self._validate_new_data(df_update)
            new_rows = list(set(df_update.index) - set(self.df.index))
            if new_rows:
                df = pd.concat([self.df, df_update[new_rows]])
                self.df = df.sort_index()
                self._save_history()

    def create_local_history(self):
        """Формирует, сохраняет и возвращает локальную версию истории дивидендных выплат."""
        self.df = download.dividends(self.ticker)
        self._save_history()


def get_dividends(tickers: list):
    """
    Сохраняет, при необходимости обновляет и возвращает дивиденды для тикеров.

    Parameters
    ----------
    tickers
        Список тикеров.

    Returns
    -------
    pd.DataFrame
        В строках - даты выплаты дивидендов.
        В столбцах - тикеры.
        Значения - выплаченные дивиденды.
    """
    df = pd.concat([LocalDividends(ticker).df for ticker in tickers], axis=1)
    df.columns = tickers
    return df


if __name__ == '__main__':
    print(get_dividends(['GAZP', 'SBERP']))
