"""Реализация менеджера данных для CPI и вспомогательные функции"""

import pandas as pd

import web
from local.data_manager import AbstractDataManager

CPI_CATEGORY = None
CPI_NAME = 'cpi'


class CPIDataManager(AbstractDataManager):
    """Реализует особенность загрузки и хранения потребительской инфляции

    Локальные данные по CPI хранятся в корне глобальной директории данных
    """
    def __init__(self):
        super().__init__(CPI_CATEGORY, CPI_NAME)

    def download_all(self):
        return web.cpi()

    def download_update(self):
        super().download_update()


def cpi():
    """Сохраняет, обновляет и загружает локальную версию данных по CPI

    Returns
    -------
    pd.Series
        В строках значения инфляции для каждого месяца
        Инфляция 1,2% за месяц соответствует 1.012
    """
    data = CPIDataManager()
    return data.value


def monthly_cpi(last_date: pd.Timestamp):
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
    help(CPIDataManager().download_all)
