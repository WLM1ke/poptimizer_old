"""Downloader and parser for MOEX Russia Net Total Return (Resident)."""

import datetime

import pandas as pd
import requests

def make_url(start_date=None, block_position=0):
    """
    Возвращает url для получения очередного блока данных по индексу 
    полной доходности MOEX.

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
            # FIXME: мы точно такую ошибку ждем? 'в написании' чего?
            #        тут же нет тикеторв? ввиду написание url?
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
  

def yield_index_blocks(start_date):
    """Yield pandas dataframes until response length is exhausted."""
    block_position = 0
    current_response = True
    while current_response:
        current_response = TotalReturn(start_date, block_position)
        block_position += len(current_response)
        yield current_response.dataframe
           
    
def get_index_history(start_date):
    """
    Возвращает историю котировок индекса полной доходности с учетом российских налогов.

    Parameters
    ----------
    start_date : datetime.date
        Начальная дата котировок. 
        
    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах цена закрытия индекса полной доходности.
    """
    result = pd.concat(yield_index_blocks(start_date))
    return result.set_index('TRADEDATE')

def get_index_history_from_start():
    """
    Возвращает историю котировок индекса полной доходности с учетом российских налогов.
    Данные запрашиваются с начала имеющейся на сервере ISS истории котировок.
    
    Предполгаемая дата начала котировок - 2003-02-26.    
    """
    return get_index_history(start_date=None)


if __name__ == '__main__':
    z = get_index_history(datetime.date(2017, 10, 1))
    print(z)
    #print(len(get_index_history(datetime.date(2017, 10, 1))))
