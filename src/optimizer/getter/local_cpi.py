"""Сохраняет, обновляет и загружает локальную версию данных по CPI.

    get_cpi()
"""

import numpy as np
import pandas as pd

from optimizer import download
from optimizer.settings import DATE, CPI
from optimizer.storage import LocalFile

CPI_FOLDER = 'macro'
CPI_FILE = 'cpi.csv'
UPDATE_PERIOD_IN_DAYS = 1


def need_update(file: LocalFile):
    """Обновление нужно, если прошло установленное число дней с момента обновления."""
    if file.updated_days_ago() > UPDATE_PERIOD_IN_DAYS:
        return True
    return False


def validate(df_old, df_updated):
    """Проверяет совпадение данных для дат, присутствующих в старом фрейме."""
    if not np.allclose(df_old, df_updated[df_old.index]):
        raise ValueError('Новые данные CPI не совпадают с локальной версией.')


def update_cpi(file: LocalFile):
    """Обновляет файл с данными, проверяя совпадение со старыми."""
    df = file.read()
    if need_update(file):
        df_updated = download.cpi()
        validate(df, df_updated)
        df = df_updated
        file.save(df)


def create_cpi(file: LocalFile):
    """Создает с нуля файл с данными."""
    df = download.cpi()
    file.save(df)


def get_cpi():
    """
    Сохраняет, обновляет и загружает локальную версию данных по CPI.

    Returns
    -------
    pd.Series
        В строках значения инфляции для каждого месяца.
        Инфляция 1,2% за месяц соответствует 1.012.
    """
    converters = {DATE: pd.to_datetime,
                  CPI: pd.to_numeric}
    data_file = LocalFile(CPI_FOLDER, CPI_FILE, converters)
    if data_file.exists():
        update_cpi(data_file)
    else:
        create_cpi(data_file)
    return data_file.read()


if __name__ == '__main__':
    print(get_cpi())
