"""Download and transform securities info to pandas DataFrames.

    Lots sizes, short names and last quotes for list of tickers:

        get_securities_info(tickers)
"""

import pandas as pd
import requests

from optimizer.settings import LAST_PRICE, LOT_SIZE, COMPANY_NAME, REG_NUMBER, TICKER


def make_url(tickers):
    url_base = ('https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?'
                'securities={tickers}')
    return url_base.format(tickers=','.join(tickers))


def get_raw_json(tickers):
    url = make_url(tickers)
    r = requests.get(url)
    result = r.json()
    validate_response(result, tickers)
    return result


def validate_response(data, tickers):
    n = len(tickers)
    msg = ('Количество тикеров в ответе не соответствует запросу'
           ' - возможно ошибка в написании')
    if len(data['securities']['data']) != n:
        raise ValueError(msg)
    if len(data['marketdata']['data']) != n:
        raise ValueError(msg)


def make_df(raw_json):
    securities = pd.DataFrame(data=raw_json['securities']['data'],
                              columns=raw_json['securities']['columns'])
    market_data = pd.DataFrame(data=raw_json['marketdata']['data'],
                               columns=raw_json['marketdata']['columns'])
    securities = securities.set_index('SECID')[['SHORTNAME', 'REGNUMBER', 'LOTSIZE']]
    market_data = pd.to_numeric(market_data.set_index('SECID')['LAST'])
    df = pd.concat([securities, market_data], axis=1)
    df.index.name = TICKER
    df.columns = [COMPANY_NAME, REG_NUMBER, LOT_SIZE, LAST_PRICE]
    return df


def get_securities_info(tickers: list):
    """
    Возвращает краткое наименование, размер лота и последнюю цену.

    Parameters
    ----------
    tickers : list
        Список тикеров.

    Returns
    -------
    pandas.DataFrame
        В строках тикеры (используется написание из выдачи ISS).
        В столбцах краткое наименование, регистрационный номер, размер лота и последняя цена.
    """
    raw_json = get_raw_json(tickers)
    return make_df(raw_json)


if __name__ == "__main__":
    print(get_securities_info(['UPRO', 'MRSB']))
