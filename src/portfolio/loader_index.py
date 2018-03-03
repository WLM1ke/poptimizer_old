"""Downloader and parser for MOEX Russia Net Total Return (Resident)."""

import datetime
import json
from urllib import request

import pandas as pd


def index_history(first=None):
    """
    Возвращает историю котировок индекса полной доходности с учетом российских налогов.

    Parameters
    ----------
    first : datetime.date
        Начальная дата котировок. Если None, то используется самая раняя дата на сервере IIS.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах цена закрытия индекса полной доходности.
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

