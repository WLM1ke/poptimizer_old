import datetime
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


def quotes_history(ticker, first=None):
    """
    Возвращает историю цен закрытия и оборотов

    Если в одну и ту же дату происходили торги в нескольких режимах, выбирается режим с максимальным оборотом
    Акций с ценой менее 1000 часто есть режим торговли дробными лотами
    У голубых фишек есть режим торговли крупными лотами
    Если сервер IIS возвращает возвращает пропущенные значения - они удаляются
    У AKRN в начале периода торгов несколько дней с пустыми значениями в цене закрытия

    Parameters
    ----------
    ticker : str
        Тикер, для которого нужны котировки
    first : datetime.date
        Начальная дата котировок. Если None, то используется самая раняя дата на сервере IIS

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
        В столбцах цена закрытия и оборот в штуках
    """

    url = ('https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/{ticker}.json?'
           + 'start={start}')

    if isinstance(first, datetime.date):
        url = url + '&from=' + str(first)

    # Сервер возвращает историю порциями
    # Параметр start указывает на начало выдачи
    # Нумерация значений идет с 0

    start = 0
    counter = True
    result = []

    while counter:
        with request.urlopen(url.format(ticker=ticker, start=start)) as response:
            data = json.load(response)

        # Ответ сервера - словарь
        # По ключу history - словарь с историей котировок
        # Во вложеном словаре есть ключи columns и data с масивами описания колонок и данными

        counter = len(data['history']['data'])
        if (counter == 0) and (start == 0):
            raise ValueError('Пустой ответ - возможно ошибка в написании')
        else:
            start += counter

        quotes = pd.DataFrame(data=data['history']['data'], columns=data['history']['columns'])
        result.append(quotes[['TRADEDATE', 'CLOSE', 'VOLUME']])

    result = pd.concat(result, ignore_index=True)
    result = result.dropna()

    result['TRADEDATE'] = pd.to_datetime(result['TRADEDATE'])
    result['CLOSE'] = pd.to_numeric(result['CLOSE'])
    result['VOLUME'] = pd.to_numeric(result['VOLUME'])

    result = result.loc[result.groupby('TRADEDATE')['VOLUME'].idxmax()]

    result = result.set_index('TRADEDATE')

    return result


def index_history(first=None):
    """
    Возвращает историю котировок индекса полной доходности с учетом российских налогов

    Parameters
    ----------
    first : datetime.date
        Начальная дата котировок. Если None, то используется самая раняя дата на сервере IIS

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
        В столбцах цена закрытия индекса полной доходности
    """

    url = ('http://iss.moex.com/iss/history/engines/stock/markets/index/boards/RTSI/securities/MCFTRR.json'
           + '?start={start}')

    if isinstance(first, datetime.date):
        url = url + '&from=' + str(first)

    # Сервер возвращает историю порциями
    # Параметр start указывает на начало выдачи
    # Нумерация значений идет с 0

    start = 0
    counter = True
    result = []

    while counter:
        with request.urlopen(url.format(start=start)) as response:
            data = json.load(response)

        # Ответ сервера - словарь
        # По ключу history - словарь с историей котировок
        # Во вложеном словаре есть ключи columns и data с масивами описания колонок и данными

        counter = len(data['history']['data'])
        if (counter == 0) and (start == 0):
            raise ValueError('Пустой ответ - возможно ошибка в написании')
        else:
            start += counter

        quotes = pd.DataFrame(data=data['history']['data'], columns=data['history']['columns'])
        result.append(quotes[['TRADEDATE', 'CLOSE']])

    result = pd.concat(result, ignore_index=True)

    result['TRADEDATE'] = pd.to_datetime(result['TRADEDATE'])
    result['CLOSE'] = pd.to_numeric(result['CLOSE'])

    result = result.set_index('TRADEDATE')

    return result


if __name__ == '__main__':
    data = security_info(['aKRN', 'gAZP', 'LKOH', 'SBER'])
    print(data)
    data = quotes_history('AKRN')
    print(data.head(10))
    print(data[99:101])
    print(data.tail())
    data = quotes_history('SBER', datetime.date(2018, 2, 9))
    print(data)
    data = index_history()
    print(data.head())
    print(data[99:101])
    print(data.tail())
    data = index_history(datetime.date(2018, 2, 9))
    print(data)
