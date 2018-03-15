"""Download and transform securities info to pandas DataFrames.

    Lots sizes, short names and last quotes for list of tickers:

        get_securities_info(tickers)
"""

import pandas as pd
import requests


def make_url(tickers):
    url_base = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?securities={tickers}'
    return url_base.format(tickers=','.join(tickers))


def get_raw_json(tickers):
    url = make_url(tickers)
    r = requests.get(url)
    result = r.json()
    validate_response(result, tickers)
    return result


def validate_response(data, tickers):
    n = len(tickers)
    msg = ('Количество тикеров в ответе не соответсвует запросу'
           ' - возможно ошибка в написании')
    if len(data['securities']['data']) != n:
        raise ValueError(msg)
    if len(data['marketdata']['data']) != n:
        raise ValueError(msg)


def make_df(raw_json):
    securities = pd.DataFrame(
        data=raw_json['securities']['data'], columns=raw_json['securities']['columns'])
    marketdata = pd.DataFrame(
        data=raw_json['marketdata']['data'], columns=raw_json['marketdata']['columns'])
    securities = securities.set_index('SECID')[['SHORTNAME', 'REGNUMBER', 'LOTSIZE']]
    marketdata = marketdata.set_index('SECID')['LAST']
    return pd.concat([securities, marketdata], axis=1)


def get_securities_info(tickers):
    """
    Возвращает краткое наименование, размер лота и последнюю цену

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
    # Ответ сервера - словарь со сложной многоуровневой структурой
    # По ключу securities - словарь с описанием инструментов
    # По ключу marketdata - словарь с последними котировками
    # В каждом из вложеных словарей есть ключи columns и data с массивами
    # описания колонок и данными
    # В массиве данных содержатся массивы для каждого запрошенного тикера
    raw_json = get_raw_json(tickers)
    return make_df(raw_json)


if __name__ == "__main__":
    print(get_securities_info(['UPRO', 'MRSB']))
