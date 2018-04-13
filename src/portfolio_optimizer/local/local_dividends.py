"""Сохраняет, обновляет и загружает локальную версию данных по дивидендам"""

import pandas as pd

from portfolio_optimizer.local.local_dividends_old import LocalDividends


def get_dividends(tickers: list):
    """
    Сохраняет, при необходимости обновляет и возвращает дивиденды для тикеров.

    Parameters
    ----------
    tickers
        Список тикеров.

    Returns
    -------
    pd.DataFrame
        В строках - даты выплаты дивидендов.
        В столбцах - тикеры.
        Значения - выплаченные дивиденды.
    """
    df = pd.concat([LocalDividends(ticker).df.to_frame() for ticker in tickers], axis=1)
    df.columns = tickers
    return df


if __name__ == '__main__':
    print(get_dividends(['GAZP', 'SBERP']))
