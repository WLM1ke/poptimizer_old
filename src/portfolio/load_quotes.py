"""Downloader and parser for quotes history."""

import datetime
import json
from urllib import request

import pandas as pd


def quotes_history(ticker, first=None):
    """
    Возвращает историю цен закрытия и оборотов

    Если в одну и ту же дату происходили торги в нескольких режимах, выбирается режим с максимальным оборотом.
    У акций с ценой менее 1000 часто есть режим торговли дробными лотами.
    У голубых фишек есть режим торговли крупными лотами.

    Parameters
    ----------
    ticker : str
        Тикер, для которого нужны котировки.
    first : datetime.date
        Начальная дата котировок. Если None, то используется самая раняя дата на сервере ISS.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах цена закрытия и оборот в штуках.
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

    result['TRADEDATE'] = pd.to_datetime(result['TRADEDATE'])
    result['CLOSE'] = pd.to_numeric(result['CLOSE'])
    result['VOLUME'] = pd.to_numeric(result['VOLUME'])

    result = result.loc[result.groupby('TRADEDATE')['VOLUME'].idxmax()]

    result = result.set_index('TRADEDATE')

    return result
