"""Downloader and parser for MOEX Russia Net Total Return (Resident)."""

import datetime

import pandas as pd
import requests


def make_url(start_date=None, block_position=0):
    """
    Возвращает url для получения очерередного блока данных по индексу полной доходности MOEX.

    Parameters
    ----------
    start_date : date.time
        Начальная дата в рамках запроса. Если тип данных отличается от date.time - данные запрашиваются с начала
        имеющейся на серевере IIS истории котировок.
    block_position : int
        Позиция курсора, начиная с которой необходимо получить очередной блок данных. При большом запросе сервер IIS
        возвращает данные блоками обычно по 100 значений. Нумерация позиций в ответе идет с 0.

    Returns
    -------
    str
        Строка url для запроса.
    """
    url = ('http://iss.moex.com/iss/history/engines/stock/markets/index/boards/RTSI/securities/MCFTRR.json'
           + '?start={start}')
    if isinstance(start_date, datetime.date):
        url = url + '&from={begin}'
    return url.format(begin=start_date, start=block_position)


def get_raw_json(start_date, block_position):
    url = make_url(start_date=start_date, block_position=block_position)
    response = requests.get(url)
    data = response.json()
    validate_respond(data, block_position)
    return data


def validate_respond(data, block_position):
    if (len(data['history']['data']) == 0) and (block_position == 0):
        raise ValueError('Пустой ответ - возможно ошибка в написании')


def get_index_history(start_date=None):
    """
    Возвращает историю котировок индекса полной доходности с учетом российских налогов.

    Parameters
    ----------
    start_date : datetime.date
        Начальная дата котировок. Если тип данных отличается от date.time - данные запрашиваются с начала
        имеющейся на серевере IIS истории котировок.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах цена закрытия индекса полной доходности.
    """
    block_position = 0
    counter = True
    result = []
    while counter:
        data = get_raw_json(start_date, block_position)
        # Ответ сервера - словарь
        # По ключу history - словарь с историей котировок
        # Во вложеном словаре есть ключи columns и data с масивами описания колонок и данными
        counter = len(data['history']['data'])
        block_position += counter
        quotes = pd.DataFrame(data=data['history']['data'], columns=data['history']['columns'])
        result.append(quotes[['TRADEDATE', 'CLOSE']])
    result = pd.concat(result)
    return result.set_index('TRADEDATE')


if __name__ == '__main__':
    print(get_index_history(datetime.date(2018, 2, 20)))
