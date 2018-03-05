"""Downloader and parser for MOEX Russia Net Total Return (Resident)."""

import datetime

import pandas as pd
import requests

#FIXME: выглядит таким образом, что block_position - обязательный параметр,
#       a start_date - необзятальный, 
#       если так, то они должны в обратном порядке идти
def make_url(start_date=None, block_position=0):
    """
    Возвращает url для получения очередного блока данных по индексу полной доходности MOEX.

    Parameters
    ----------
    start_date : date.time
        Начальная дата в рамках запроса. Если тип данных отличается от date.time - данные запрашиваются с начала
        имеющейся на серевере ISS истории котировок.
    block_position : int
        Позиция курсора, начиная с которой необходимо получить очередной блок данных. При большом запросе сервер ISS
        возвращает данные блоками обычно по 100 значений. Нумерация позиций в ответе идет с 0.

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
        # start_date желательно приводить в нужный формат явным образом 
        # https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
        # в прошлом коде формат совпадает "наугад" по умолчаниям
        url = url + f'&from={start_date:%Y-%m-%d}'
    return url


def get_raw_json(start_date, block_position):
    url = make_url(start_date=start_date, block_position=block_position)
    response = requests.get(url)
    return response.json()

class TotalReturn:
    """Представление ответа сервера в виде класса."""    
        # Ответ сервера - словарь
        # По ключу history - словарь с историей котировок
        # Во вложеном словаре есть ключи columns и data с масивами описания колонок и данными

    def __init__(self, start_date, block_position):
        self.data = get_raw_json(start_date, block_position)        
        self.validate(block_position) 

    def validate(self, block_position):
        if len(self) == 0 and block_position == 0:
            raise ValueError('Пустой ответ - возможно ошибка в написании')
        
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
        return df[['TRADEDATE', 'CLOSE']]
        
    
def get_index_history(start_date=None):
    """
    Возвращает историю котировок индекса полной доходности с учетом российских налогов.

    Parameters
    ----------
    start_date : datetime.date
        Начальная дата котировок. Если тип данных отличается от date.time - данные запрашиваются с начала
        имеющейся на серевере ISS истории котировок.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах цена закрытия индекса полной доходности.
    """
    block_position = 0
    current_response = True
    result = pd.DataFrame()
    while current_response:
        current_response = TotalReturn(start_date, block_position)
        block_position += len(current_response)
        result = pd.concat([result, current_response.dataframe])
    return result.set_index('TRADEDATE')


if __name__ == '__main__':
    z = get_index_history(datetime.date(2017, 10, 1))
    print(z)
    #print(len(get_index_history(datetime.date(2017, 10, 1))))
