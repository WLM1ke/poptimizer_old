"""Загрузка данных по месячному индексу потребительских цен сайта www.gks.ru"""

from datetime import date

import pandas as pd

from portfolio_optimizer.settings import CPI, DATE

URL_CPI = 'http://www.gks.ru/free_doc/new_site/prices/potr/I_ipc.xlsx'
PARSING_PARAMETERS = dict(sheet_name='ИПЦ', header=3, skiprows=[4], skip_footer=3)
NUM_OF_MONTH = 12
FIRST_YEAR = 1991
FIRST_MONTH = 'январь'


def validate(df: pd.DataFrame):
    """Проверка заголовков таблицы"""
    months, _ = df.shape
    first_year = df.columns[0]
    first_month = df.index[0]
    if months != NUM_OF_MONTH:
        raise ValueError('Таблица должна содержать 12 строк с месяцами')
    if first_year != FIRST_YEAR:
        raise ValueError('Первый год должен быть 1991')
    if first_month != FIRST_MONTH:
        raise ValueError('Первый месяц должен быть январь')


def parse_xls(url: str):
    """Загружает, проверяет и преобразует xls-файл"""
    df = pd.read_excel(url, **PARSING_PARAMETERS)
    validate(df)
    size = df.shape[0] * df.shape[1]
    first_year = df.columns[0]
    # Данные должны быть в виде Series
    index = pd.DatetimeIndex(name=DATE, freq='M', start=date(first_year, 1, 31), periods=size)
    flat_data = df.values.reshape(size, order='F')
    df = pd.Series(flat_data, index=index, name=CPI).dropna()
    # Данные должны быть не в процентах, а в долях
    return df.div(100)


def cpi():
    """
    Загружает данные по месячному CPI с сайта ФСГС и возвращает

    1,2% соответствует 1,012

    Returns
    -------
    pd.Series
        В строках значения инфляции для каждого месяца.
    """
    return parse_xls(URL_CPI)


if __name__ == '__main__':
    print(cpi())
