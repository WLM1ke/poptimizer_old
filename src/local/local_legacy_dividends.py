"""Загрузка 'старой версии' дивидендов для реализации xlsx модели"""

from functools import lru_cache

import pandas as pd

from settings import DATA_PATH

FILE_PATH = DATA_PATH / 'legacy_dividends' / 'dividends.xlsx'
LEGACY_SHEET_NAME = 'Dividends'


@lru_cache(maxsize=1)
def legacy_dividends(tickers: tuple):
    """
    Возвращает ряды годовых дивидендов для тикеров

    Основывается на статических локальных данных, которые хранятся в xlsx файле. Данная функция нужна для первоначальной
    реализации и сопоставления с xlsx версией модели оптимизации. При дальнейшем развитии будет использоваться более
    современная реализация на основе динамического обновления данных из интернета

    Parameters
    ----------
    tickers
        Список тикеров

    Returns
    -------
    pandas.DataFrame
        В строках даты годы
        В столбцах цены годовые дивиденды для тикеров
    """

    df = pd.read_excel(FILE_PATH, sheet_name=LEGACY_SHEET_NAME, header=0, index_col=0)
    return df.loc[tickers, :].transpose()


if __name__ == '__main__':
    print(legacy_dividends(('AKRN',)))
