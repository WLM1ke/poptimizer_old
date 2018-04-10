"""Load local data for legacy dividends history and returns pandas DataFrames.

    get_legacy_dividends(tickers)
"""

import pandas as pd

from portfolio_optimizer.local import storage

DATA_PATH = storage.make_data_path('legacy_dividends', 'dividends.xlsx')
LEGACY_SHEET_NAME = 'Dividends'


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

    df = pd.read_excel(DATA_PATH, sheet_name=LEGACY_SHEET_NAME, header=0, index_col=0)
    return df.transpose()[tickers]


if __name__ == '__main__':
    print(get_legacy_dividends(['AKRN']))
