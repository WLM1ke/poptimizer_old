"""Сохраняет, обновляет и загружает локальную версию данных по CPI.

    get_cpi()
"""

import time
from os import path

import numpy as np
import pandas as pd

from portfolio import download
from portfolio import settings
from portfolio.settings import DATE, CPI

FILE_NAME = 'CPI.csv'
UPDATE_PERIOD_IN_SECONDS = 60 * 60 * 24


def cpi_path():
    """Формирует и при необходимости создает путь к файлу с данными."""
    return settings.make_data_path(None, FILE_NAME)


def save_cpi(df):
    """Сохраняет файл с данными."""
    df.to_csv(cpi_path(), index=True, header=True)


def load_cpi():
    """Загружает данные из локальной версии и возвращает их."""
    df = pd.read_csv(cpi_path(),
                     converters={DATE: pd.to_datetime, CPI: pd.to_numeric},
                     header=0,
                     engine='python',
                     sep='\s*,')
    df = df.set_index(DATE)
    return df[CPI]


def cpi_need_update():
    """Обновление нужно, если прошло установленное число секунд с момента обновления."""
    if time.time() - path.getmtime(cpi_path()) > UPDATE_PERIOD_IN_SECONDS:
        return True
    return False


def validate(df_old, df_updated):
    """Проверяет совпадение данных для дат, присутствующих в старом фрейме."""
    if not np.allclose(df_old, df_updated[df_old.index]):
        raise ValueError('Новые данные CPI не совпадают с локальной версией.')


def update_cpi():
    df = load_cpi()
    if cpi_need_update():
        df_updated = download.cpi()
        validate(df, df_updated)
        df = df_updated
        save_cpi(df)
    return df


def create_cpi():
    """Создает с нуля файл с данными и возвращает серию с инфляцией."""
    df = download.cpi()
    save_cpi(df)
    return df


def get_cpi():
    """
    Сохраняет, обновляет и загружает локальную версию данных по CPI.

    Returns
    -------
    pd.Series
        В строках значения инфляции для каждого месяца.
    """
    if cpi_path().exists():
        return update_cpi()
    else:
        return create_cpi()


if __name__ == '__main__':
    print(get_cpi())
