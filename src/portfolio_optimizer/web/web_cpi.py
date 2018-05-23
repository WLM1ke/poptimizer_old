"""Загрузка данных по месячному индексу потребительских цен сайта www.gks.ru"""

from datetime import date

import pandas as pd

from portfolio_optimizer.web.labels import DATE, CPI

URL_CPI = 'http://www.gks.ru/free_doc/new_site/prices/potr/I_ipc.xlsx'
PARSING_PARAMETERS = dict(sheet_name='ИПЦ', header=3, skiprows=[4], skipfooter=3)
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
    df = df.transpose().stack()
    first_year = df.index[0][0]
    df.index = pd.DatetimeIndex(name=DATE, freq='M', start=date(first_year, 1, 31), periods=len(df))
    df.name = CPI
    # Данные должны быть не в процентах, а в долях
    return df.div(100)


def cpi():
    """
    Загружает и возвращает данные по месячному CPI с сайта ФСГС

    1,2% соответствует 1,012

    Returns
    -------
    pd.Series
        В строках значения инфляции для каждого месяца.
    """
    return parse_xls(URL_CPI)


if __name__ == '__main__':
    print(cpi())
