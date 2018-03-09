"""Download and transform dividends data to pandas DataFrames.

    Single ticker close dates and dividends:

        get_ticker_dividends(ticker)
"""

import urllib.error
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup


class Dividends:
    # это параметры парсинга? лучше будут параметрами функции где они используются
    table_index = 2     
    date_index = 0
    date_name = 'Дата закрытия реестра'
    dividend_index = 2
    dividend_name = 'Дивиденд (руб.)'

    def __init__(self, ticker):
        self.ticker = ticker
        self._html_table = None

    # здесь OK!    
    @property
    def url(self):
        return f'http://www.dohod.ru/ik/analytics/dividend/{self.ticker.lower()}'

    @property
    def html(self):
        # EP: must be separate testable fucntion!!!
        try:
            # *requests* fails on SSL, using *urllib.request*
            with urllib.request.urlopen(self.url) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise urllib.error.URLError(f'Неверный url: {self.url}')

    @property
    def html_table(self):
        # Класс нужно ограничить функционалом - получить и закешироват url, все остальное - это либо другие функции или классы.  
        # Происходит несколько вызовов - запоминается значение, чтобы не дергать url повторно
        if self._html_table:
            return self._html_table
        else:
            # отдельная функция, ей сейчас неявно передается параметр
            soup = BeautifulSoup(self.html, 'lxml')
            self._html_table = soup.find_all('table')[self.table_index]
            return self._html_table

    def _validate_table_header(self):
        # зона поиска должна быть конкретная таблица, а не все tr/th  
        names = [column.string for column in self.html_table.find(name='tr').find_all(name='th')]
        if names[self.date_index] != self.date_name or names[self.dividend_index] != self.dividend_name:
            raise ValueError(f'Некоректные заголовки таблицы дивидендов {self.ticker}')

    @property
    def table_rows(self):
        # Строки с прогнозом имеют class = forecast, а с фактом - класс отсутсвует
        return self.html_table.find_all(name='tr', class_=None)[1:]

    
    # тут вообще начинается жесть - название как у функции, тип property
    @property
    def parse_rows(self):
        self._validate_table_header()
        data = []
        for html_row in self.table_rows:
            row = [column.string for column in html_row.find_all('td')]
            data.append([row[self.date_index], row[self.dividend_index]])
        return data

    @property
    def df(self):
        df = pd.DataFrame(data=self.parse_rows,
                          columns=['CLOSE_DATE', 'DIVIDENDS'])
        # apply или map будут покороче
        df['CLOSE_DATE'] = pd.to_datetime(df['CLOSE_DATE'])
        df['DIVIDENDS'] = pd.to_numeric(df['DIVIDENDS'])
        return df.set_index('CLOSE_DATE').sort_index()

# вот на этой функции надо все и писать, класс в существующем виде очень запутанный
def get_dividends(ticker):
    return Dividends(ticker).df


if __name__ == '__main__':
    print(get_dividends('CHMF'))
