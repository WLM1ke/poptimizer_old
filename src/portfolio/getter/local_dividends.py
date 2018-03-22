"""Load and update local data for dividends history and returns pandas DataFrames.

    get_dividends(tickers)
    get_legacy_dividends(tickers)
"""

import time
from os import path

import numpy as np
import pandas as pd

from portfolio import settings, download
from portfolio.settings import DATE, DIVIDENDS

LEGACY_DIVIDENDS_FILE = 'dividends.xlsx'
LEGACY_SHEET_NAME = 'Dividends'
DIVIDENDS_FOLDER = 'dividends'
UPDATE_PERIOD_IN_SECONDS = 60 * 60 * 24


def legacy_dividends_path():
    """Файл со 'старыми' данными по дивидендам хранится в корне каталога данных."""
    return settings.make_data_path(None, LEGACY_DIVIDENDS_FILE)


class LocalDividends:
    """Реализует хранение, обновление и хранение локальных данных по индексу дивидендам."""
    _data_folder = DIVIDENDS_FOLDER
    _load_converter = {DATE: pd.to_datetime, DIVIDENDS: pd.to_numeric}
    _data_columns = DIVIDENDS

    def __init__(self, ticker: str):
        self.ticker = ticker
        if self.local_data_path.exists():
            self._df = self.load_local_history()
            self._df = self.update_local_history()
        else:
            self._df = self.create_local_history()

    def __call__(self):
        return self._df

    @property
    def local_data_path(self):
        """Возвращает и при необходимости создает путь к файлу с котировками."""
        return settings.make_data_path(self._data_folder, f'{self.ticker}.csv')

    def _save_history(self):
        """Сохраняет локальную версию данных в csv-файл с именем тикера.

        Флаги заголовков необходимы для поддержки сохранения серий, а не только датафреймов."""
        self._df.to_csv(self.local_data_path, index=True, header=True)

    def load_local_history(self):
        """Загружает историю котировок из локальных данных.

        Значение sep гарантирует загрузку данных с добавленными PyCharm пробелами
        """
        df = pd.read_csv(self.local_data_path,
                         converters=self._load_converter,
                         header=0,
                         engine='python',
                         sep='\s*,')
        self._df = df.set_index(DATE)
        return self._df[self._data_columns]

    def need_update(self):
        """Обновление требуется по прошествии фиксированного количества секунд."""
        if time.time() - path.getmtime(self.local_data_path) > UPDATE_PERIOD_IN_SECONDS:
            return True
        return False

    def _validate_new_data(self, df_new):
        """Проверяем, что старые данные совпадают с новыми."""
        common_rows = list(set(self._df.index) & set(df_new.index))
        if not np.allclose(self._df.loc[common_rows], df_new.loc[common_rows]):
            raise ValueError(f'Новые данные по дивидендам {self.ticker} не совпадают с локальной версией.')

    def update_local_history(self):
        """Обновляет локальные данные данными из интернета и возвращает полную историю дивидендных выплат."""
        if self.need_update():
            df_update = download.dividends(self.ticker)
            self._validate_new_data(df_update)
            new_rows = list(set(df_update.index) - set(self._df.index))
            if new_rows:
                df = pd.concat([self._df, df_update[new_rows]])
                self._df = df.sort_index()
                self._save_history()
        return self._df

    def create_local_history(self):
        """Формирует, сохраняет и возвращает локальную версию истории дивидендных выплат."""
        self._df = download.dividends(self.ticker)
        self._save_history()
        return self._df


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
    df = pd.concat([LocalDividends(ticker)() for ticker in tickers], axis=1)
    df.columns = tickers
    return df


def get_legacy_dividends(tickers: list):
    """
    Возвращает ряды годовых дивидендов для тикеров.

    Основывается на статических локальных данных, которые хранятся в xlsx файле. Данная функция нужна для первоначальной
    реализации и сопоставления с xlsx версией модели оптимизации. При дальнейшем развитии будет использоваться более
    современная реализация на основе динамического обновления данных из интернета.

    Parameters
    ----------
    tickers
        Список тикеров.

    Returns
    -------
    pandas.DataFrame
        В строках даты годы.
        В столбцах цены годовые дивиденды для тикеров.
    """

    df = pd.read_excel(legacy_dividends_path(), sheet_name=LEGACY_SHEET_NAME, header=0, index_col=0)
    return df.transpose()[tickers]


if __name__ == '__main__':
    print(get_dividends(['GAZP', 'MRKC']))
