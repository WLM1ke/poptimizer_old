"""Сохраняет, обновляет и загружает локальную версию данных по CPI"""

import pandas as pd

from portfolio_optimizer import web
from portfolio_optimizer.local.data_manager import DataManager

CPI_CATEGORY = 'macro'
CPI_NAME = 'cpi'


class CPIDataManager(DataManager):
    """Реализует особенность загрузки потребительской инфляции"""

    def __init__(self):
        super().__init__(CPI_CATEGORY, CPI_NAME, web.cpi)


def cpi():
    """
    Сохраняет, обновляет и загружает локальную версию данных по CPI

    Returns
    -------
    pd.Series
        В строках значения инфляции для каждого месяца
        Инфляция 1,2% за месяц соответствует 1.012
    """
    data = CPIDataManager()
    return data.get()


def cpi_to_date(last_date: pd.Timestamp):
    """Месячная инфляция с учетом даты окончания

    Даты, на которую дана месячная инфляция соответствует дню месяца из last_date
    Если дата после окончания статистики, то она продлевается исходя из последней годовой инфляции

    Parameters
    ----------
    last_date
        Конечная дата в ряде данных месячной инфляции
    Returns
    -------
    pd.Series
        В строках значения инфляции для каждого месяца
        Инфляция 1,2% за месяц соответствует 1.012
    """
    df = cpi()
    index = pd.DatetimeIndex(name=df.index.name,
                             freq='M',
                             start=df.index[0],
                             end=last_date + pd.DateOffset(day=31))
    df = df.reindex(index)
    df = df.fillna(df.shift(12))
    index = index.map(pd.DateOffset(day=last_date.day))
    df.index = index
    return df


if __name__ == '__main__':
    print(cpi_to_date(pd.Timestamp('2018-07-19')))
