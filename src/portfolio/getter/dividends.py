"""Load and update local data for dividends history and returns pandas DataFrames."""

import time
from os import path

import numpy as np
import pandas as pd

from portfolio import settings, download
from portfolio.getter.history import LocalQuotes
from portfolio.settings import DATE, DIVIDENDS

LEGACY_DIVIDENDS_FILE = 'dividends.xlsx'
LEGACY_SHEET_NAME = 'Dividends'
DIVIDENDS_FOLDER = 'dividends'
UPDATE_PERIOD_IN_SECONDS = 60 * 60 * 24


def legacy_dividends_path():
    """Файл со 'старыми' данными по дивидендам хранится в корне каталога данных."""
    return settings.make_data_path(None, LEGACY_DIVIDENDS_FILE)


class LocalDividends(LocalQuotes):
    """Реализует хранение, обновление и хранение локальных данных по индексу дивидендам."""
    _data_folder = DIVIDENDS_FOLDER
    _load_converter = {DATE: pd.to_datetime, DIVIDENDS: pd.to_numeric}
    _data_columns = DIVIDENDS

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
    return pd.concat([LocalDividends(ticker)() for ticker in tickers], axis=1)


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
