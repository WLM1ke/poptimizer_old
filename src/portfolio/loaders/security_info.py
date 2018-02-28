import json
from urllib import request

import pandas as pd


def security_info(tickers):
    """
    Возвращает краткое наименование, размер лота и последнюю цену

    Parameters
    ----------
    tickers : str or list of str
        Тикер или список тикеров

    Returns
    -------
    pandas.DataFrame
        В строках тикеры (используется написание из выдачи ISS)
        В столбцах краткое наименование, размер лота и последняя цена
    """

    if isinstance(tickers, str):
        tickers = [tickers]

    url = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?securities={tickers}'
    with request.urlopen(url.format(tickers=','.join(tickers))) as response:
        data = json.load(response)

    # Ответ сервера - словарь со сложной многоуровневой структурой
    # По ключу securities - словарь с описанием инструментов
    # По ключу marketdata - словарь с последними котировками
    # В кажом из вложеных словарей есть ключи columns и data с масивами описания колонок и данными
    # В массиве данных содержатся массивы для каждого запрошенного тикера

    if len(data['securities']['data']) != len(tickers):
        raise ValueError('Количество тикеров в ответе не соответсвует запросу - возможно ошибка в написании')
    elif len(data['marketdata']['data']) != len(tickers):
        raise ValueError('Количество тикеров в ответе не соответсвует запросу - возможно ошибка в написании')

    securities = pd.DataFrame(data=data['securities']['data'], columns=data['securities']['columns'])
    marketdata = pd.DataFrame(data=data['marketdata']['data'], columns=data['marketdata']['columns'])

    securities = securities.set_index('SECID')[['SHORTNAME', 'LOTSIZE']]
    marketdata = marketdata.set_index('SECID')['LAST']
    result = pd.concat([securities, marketdata], axis=1)

    return result


if __name__ == '__main__':
    data = security_info(['aKRN', 'gAZP', 'LKOH', 'SBER'])
    print(data)
