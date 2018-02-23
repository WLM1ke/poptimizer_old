import json
from urllib import request

import pandas as pd


def security_info(ticker):
    if not isinstance(ticker, str):
        raise ValueError('Тикер должен быть строкой')

    url = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json'
    with request.urlopen(url.format(ticker=ticker)) as response:
        data = json.load(response)

    if len(data) != 3:
        raise ValueError('В словаре данных должно быть три поля')
    elif len(data['securities']['data']) == 0:
        raise ValueError('Неверный тикер')

    result = pd.Series(name=ticker)
    data_fields = [['Name', 'securities', 'SHORTNAME'],
                   ['Lot size', 'securities', 'LOTSIZE'],
                   ['Last price', 'marketdata', 'LAST']]
    for index, block, field in data_fields:
        position = data[block]['columns'].index(field)
        if len(data[block]['data']) != 1:
            raise ValueError('В списке должен быть один элемент')
        result[index] = data[block]['data'][0][position]

    return result


if __name__ == '__main__':
    data = security_info('GAZP')
    print(data)
