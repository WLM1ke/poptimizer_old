"""Сохраняет, обновляет и загружает локальную версию данных по CPI"""

import pandas as pd

from portfolio_optimizer import web
from portfolio_optimizer.local.data_manager import DataManager

CPI_CATEGORY = 'macro'
CPI_NAME = 'cpi'


def cpi():
    """
    Сохраняет, обновляет и загружает локальную версию данных по CPI

    Returns
    -------
    pd.Series
        В строках значения инфляции для каждого месяца
        Инфляция 1,2% за месяц соответствует 1.012
    """
    data = DataManager(CPI_CATEGORY, CPI_NAME, web.cpi)
    return data.get()


if __name__ == '__main__':
    print(cpi())
