"""Load and update local data for dividends history and returns pandas DataFrames."""

import pandas as pd

from portfolio import settings

LEGACY_DIVIDENDS_FILE = 'dividends.xlsx'


def legacy_dividends_path():
    return settings.make_data_path(None, LEGACY_DIVIDENDS_FILE)


def get_legacy_dividends(tickers: list) -> pd.DataFrame:
    """
    Возвращает годовые дивиденды для тикеров.

    Основывается на статичеких локальных данных, которые хранятьсяв xlsx файле. Данная функция нужна для первоначальной
    реализации и сопоставления с xlsx версией модели оптимизации. При дальнейшем развитии будет использоваться более
    современная реализациия на основе динамического обновления данных из интернета.

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

    df = pd.read_excel(legacy_dividends_path(), sheet_name='Dividends', header=0, index_col=0)
    return df.transpose()[tickers]


if __name__ == '__main__':
    print(get_legacy_dividends(['AKRN', 'RTKMP']))
