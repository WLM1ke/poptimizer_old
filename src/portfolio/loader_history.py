"""Downloader and parser for MOEX Russia Net Total Return (Resident)."""

import datetime

import pandas as pd
import requests


def index_url(start_date=None, block_position=0):
    """
    Возвращает url для получения очередного блока данных по индексу полной доходности MOEX.

    Parameters
    ----------
    start_date : date.time or None
        Начальная дата котировок. Если предоставлено значение None 
        - данные запрашиваются с начала имеющейся на сервере ISS 
        истории котировок.
    block_position : int
        Позиция курсора, начиная с которой необходимо получить очередной блок 
        данных. При большом запросе сервер ISS возвращает данные блоками обычно 
        по 100 значений. Нумерация позиций в ответе идет с 0.

    Returns
    -------
    str
        Строка url для запроса.
    """
    url = ('http://iss.moex.com/iss/history/engines/stock/markets/index/boards/RTSI/securities/MCFTRR.json'
           f'?start={block_position}')
    if start_date:
        if not isinstance(start_date, datetime.date):
            raise TypeError(start_date)
        url = url + f'&from={start_date:%Y-%m-%d}'
    return url


def compose_ticker_url_function(ticker):
    base_url = f'https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/{ticker}.json'

    def ticker_url(start_date=None, block_position=0):
        url = base_url + f'?start={block_position}'
        if start_date:
            if not isinstance(start_date, datetime.date):
                raise TypeError(start_date)
            url = url + f'&from={start_date:%Y-%m-%d}'
        return url

    return ticker_url


class TotalReturn:
    """Представление ответа сервера в виде класса."""

    # Ответ сервера - словарь
    # По ключу history - словарь с историей котировок
    # Во вложеном словаре есть ключи columns и data с масивами описания колонок и данными

    def __init__(self, url_function, start_date, block_position):
        self.data = self.get_raw_json(url_function, start_date, block_position)
        self.validate(block_position)

    @staticmethod
    def get_raw_json(url_function, start_date, block_position):
        url = url_function(start_date=start_date, block_position=block_position)
        response = requests.get(url)
        return response.json()

    def validate(self, block_position):
        if len(self) == 0 and block_position == 0:
            raise ValueError('Пустой ответ - возможно ошибка в url')

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return self.__len__() > 0

    @property
    def values(self):
        return self.data['history']['data']

    @property
    def columns(self):
        return self.data['history']['columns']

    @property
    def dataframe(self):
        df = pd.DataFrame(data=self.values, columns=self.columns)
        # Для котировков акций нужная колонка VOLUME, а для индекса она отсутсвует
        columns = list({'TRADEDATE', 'CLOSE', 'VOLUME'} & set(self.columns))
        return df[columns]


def yield_data_blocks(url_function, start_date):
    """Yield pandas DataFrames until response length is exhausted."""
    block_position = 0
    current_response = True
    while current_response:
        current_response = TotalReturn(url_function, start_date, block_position)
        block_position += len(current_response)
        yield current_response.dataframe


def get_index_history(start_date):
    """
    Возвращает историю котировок индекса полной доходности с учетом российских налогов.

    Parameters
    ----------
    start_date : datetime.date or None
        Начальная дата котировок. 
        
    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах цена закрытия индекса полной доходности.
    """
    result = pd.concat(yield_data_blocks(index_url, start_date))
    return result.set_index('TRADEDATE')


def get_index_history_from_start():
    """
    Возвращает историю котировок индекса полной доходности с учетом российских налогов.

    Данные запрашиваются с начала имеющейся на сервере ISS истории котировок.
    Предполгаемая дата начала котировок - 2003-02-26.    
    """
    return get_index_history(start_date=None)


def get_ticker_history(ticker, start_date):
    """
    Возвращает историю котировок тикера.

    Parameters
    ----------
    ticker : str
        Тикер.

    start_date : datetime.date or None
        Начальная дата котировок.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах цена закрытия и оборот в штуках.
    """
    result = pd.concat(yield_data_blocks(compose_ticker_url_function(ticker), start_date), ignore_index=True)
    # Часто объемы не распознаются, как численные значения
    result['VOLUME'] = pd.to_numeric(result['VOLUME'])
    # Для каждой даты выбирается режим торгов с максимальным оборотом
    result = result.loc[result.groupby('TRADEDATE')['VOLUME'].idxmax()]

    return result.set_index('TRADEDATE')


def get_ticker_history_from_start(ticker):
    """
    Возвращает историю котировок тикера.

    Данные запрашиваются с начала имеющейся на сервере ISS истории котировок.
    Начальная дата различается для разных тикеров.
    """
    return get_ticker_history(ticker, start_date=None)


if __name__ == '__main__':
    z = get_ticker_history('MOEX', datetime.date(2017, 10, 2))
    print(z)
    # print(len(get_index_history(datetime.date(2017, 10, 1))))
