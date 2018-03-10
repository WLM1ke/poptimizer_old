"""Download and transform daily quotes to pandas DataFrames.

   1. Single ticker daily price and volumes:

        get_quotes_history(ticker, start_date)
        get_quotes_history_from_start(ticker)
   
   2. MOEX Russia Net Total Return (Resident) Index:

        get_index_history(start_date)
        get_index_history_from_start()
"""

import datetime

import pandas as pd
import requests


def get_json(url: str):
    """Return json found at *url*."""
    response = requests.get(url)
    return response.json()


def make_url(base: str, ticker: str, start_date=None, block_position=0):
    """Create url based on components.
    
    Parameters
    ----------
    base
        Основная часть url.
    ticker
        Наименование тикера.
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
    if not base.endswith('/'):
        base += '/'
    url = base + f'{ticker}.json'
    query_args = [f'start={block_position}']
    if start_date:
        if not isinstance(start_date, datetime.date):
            raise TypeError(start_date)
        query_args.append(f"from={start_date:%Y-%m-%d}")
    arg_str = '&'.join(query_args)
    return f'{url}?{arg_str}'


class Quotes:
    """
    Представление ответа сервера по отдельному тикеру.
    """
    base = 'https://iss.moex.com/iss/history/engines/stock/markets/shares/securities'

    def __init__(self, ticker, start_date):        
        self.ticker, self.start_date = ticker, start_date
        self.block_position = 0 
        self.load()
        
    @property    
    def url(self):
        return make_url(self.base, self.ticker, 
                        self.start_date, self.block_position)
        
    def load(self):    
        self.data = get_json(self.url)
        self._validate() 
        
    def _validate(self):
        if self.block_position == 0 and len(self) == 0:
            raise ValueError(f'Пустой ответ. Проверьте запрос: {self.url}')
        
    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return self.__len__() > 0
    
    #  В ответе сервера есть словарь:
    #   - по ключу history - словарь с историей котировок
    #   - во вложеном словаре есть ключи columns и data с масивами описания 
    #     колонок и данными.  

    @property
    def values(self):
        return self.data['history']['data']

    @property
    def columns(self):
        return self.data['history']['columns']      

    @property
    def df(self):
        """Raw dataframe from *self.data['history']*"""
        return pd.DataFrame(data=self.values, columns=self.columns)

    # WONTFIX: для итератора необходимы два метода: __iter__() и __next__() 
    #          возможно, переход к следующему элементу может быть по-другому 
    #          распределен между этими методами    
    def __iter__(self):
        return self   

    def __next__(self):
        # если блок непустой
        if self:
            # используем текущий результат парсинга
            current_dataframe = self.dataframe  
            # перещелкиваем сдаиг на следующий блок и получаем новые данные 
            self.block_position += len(self)
            self.load()
            # выводим текущий результат парсинга
            return current_dataframe 
        else:
            raise StopIteration

    @property
    def dataframe(self):
        df = self.df
        df['TRADEDATE'] = pd.to_datetime(df['TRADEDATE'])
        df['CLOSE'] = pd.to_numeric(df['CLOSE'])
        df['VOLUME'] = pd.to_numeric(df['VOLUME'])
        return df[['TRADEDATE', 'CLOSE', 'VOLUME']]


class TotalReturn(Quotes):
    """
    Представление ответа сервера - данные по индексу полной доходности MOEX.
       
    """
    base = 'http://iss.moex.com/iss/history/engines/stock/markets/index/boards/RTSI/securities'
    ticker = 'MCFTRR'
    
    def __init__(self, start_date):
        super().__init__(self.ticker, start_date)
        
    @property
    def dataframe(self):
        df = self.df
        df['TRADEDATE'] = pd.to_datetime(df['TRADEDATE'])
        df['CLOSE'] = pd.to_numeric(df['CLOSE'])
        return df[['TRADEDATE', 'CLOSE']].set_index('TRADEDATE')
    

def get_index_history(start_date):
    """
    Возвращает котировки индекса полной доходности с учетом российских налогов
    начиная с даты *start_date*.

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
    return pd.concat(TotalReturn(start_date))


def get_index_history_from_start():
    """
    Возвращает котировки индекса полной доходности с учетом российских налогов 
    с начала информации. Предполагаемая дата начала котировок: 2003-02-26.    
    """
    return get_index_history(start_date=None)


def get_quotes_history(ticker, start_date):
    """
    Возвращает историю котировок тикера начиная с даты *start_date*.

    Parameters
    ----------
    ticker : str
        Тикер, например, 'MOEX'.

    start_date : datetime.date or None
        Начальная дата котировок.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах [CLOSE, VOLUME] цена закрытия и оборот в штуках .
    """
    gen = Quotes(ticker, start_date)
    df = pd.concat(gen, ignore_index=True)
    # для каждой даты выбирается режим торгов с максимальным оборотом
    df = df.loc[df.groupby('TRADEDATE')['VOLUME'].idxmax()]
    return df.set_index('TRADEDATE')


def get_quotes_history_from_start(ticker):
    """
    Возвращает историю котировок тикера с начала информации.
    Начальная дата различается для разных тикеров.
    """
    return get_quotes_history(ticker, start_date=None)


if __name__ == '__main__':
    assert len(list(Quotes('AKRN', datetime.date(2017, 3, 1)))) >= 4
    h = get_quotes_history('MOEX', datetime.date(2017, 10, 2))
    print(h.head())
    print(h.tail())
    z = get_index_history(start_date=datetime.date(2017, 10, 2))
    print(z.head())
    print(z.tail())
