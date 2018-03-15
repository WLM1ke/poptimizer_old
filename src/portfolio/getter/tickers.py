"""Load aliases for ticker and update local securities info data.

    get_tickers(ticker)
"""

import pandas as pd

from portfolio import download
from portfolio.getter import security_info


def get_or_create_local_securityes_info(ticker):
    if security_info.securities_info_path().exists():
        info = security_info.load_securities_info()
    else:
        info = security_info.create_local_security_info([ticker])
    return info


def get_tickers(ticker: str) -> list:
    """
    Возвращает список тикеров аналогов для заданного тикера.

    Parameters
    ----------
    ticker
        Тикер.

    Returns
    -------
    list
        Список тикеров аналогов заданного тикера, включая его самого.
    """
    info = get_or_create_local_securityes_info(ticker)
    if (ticker in info.index) and pd.notna(info.loc[ticker, 'TICKERS']):
        # если тикер и информация по долнительным тикерам есть, то берем ее из локальной версии
        tickers = info.loc[ticker, 'TICKERS']
    elif ticker in info.index:
        # если тикер присутсувет, но информации по долнительным тикерам нет,
        # то загружаем информацию и сохраняем локально
        tickers = download.tickers(info.loc[ticker, 'REGNUMBER'])
        info.loc[ticker, 'TICKERS'] = tickers
        security_info.save_security_info(info)
    else:
        # Если тикера нет в локальной версии, то загружаем информацию,
        # загружаем и добовляем информацию по дополнительным тикерам, объединяем с текущей информацией и сохраняем
        info_update = security_info.download_securities_info([ticker])
        tickers = download.tickers(info_update.loc[ticker, 'REGNUMBER'])
        info_update.loc[ticker, 'TICKERS'] = tickers
        info = pd.concat([info, info_update])
        security_info.save_security_info(info)
    return tickers.split(sep=' ')


if __name__ == '__main__':
    print(get_tickers('UPRO'))
