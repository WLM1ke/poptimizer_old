"""Download and transform dividends data to pandas DataFrames.

   Single ticker close dates and dividends:

       get_dividends(ticker)

"""

import urllib.error
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup

# номер таблицы с дивидендами в документе
TABLE_INDEX = 2
# позиции и наименования ключевых столбцов 
TH_DATE = 'Дата закрытия реестра'
TH_VALUE = 'Дивиденд (руб.)'
DATE_COLN = 0
VALUE_COLN = 2


def get_html(url):
    try:
        # *requests* fails on SSL, using *urllib.request*
        with urllib.request.urlopen(url) as response:
            # EP: это плохо тестируется и перескакивает между уровнями
            # return BeautifulSoup(response.read(), 'lxml')
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise urllib.error.URLError(f'Неверный url: {url}')
        else:
            raise error


def make_url(ticker: str):
    # Обычно тикеры пишутся всеми большими буквами, но в url они должны быть маленькими
    ticker = ticker.lower()
    return f'http://www.dohod.ru/ik/analytics/dividend/{ticker}'


def pick_table(html: str, n: int=TABLE_INDEX):
    soup = BeautifulSoup(html, 'lxml')
    return soup.find_all('table')[n]


class RowParser:
    def __init__(self, row, tag='td'):
        self.columns=[column.string for column in row.find_all(tag)]
    
    @property
    def date(self):
        return self.columns[DATE_COLN] #0
    
    @property    
    def value(self):     
        return self.columns[VALUE_COLN] #2
        

def parse_table_rows(table):
    def validate_table_header(header):
        r = RowParser(header, 'th')
        if r.date != TH_DATE or r.value != TH_VALUE:
            raise ValueError('Некоректные заголовки таблицы дивидендов.')
    # Строки с прогнозом имеют class = forecast, а у заголовка и факта 
    # - класс отсутсвует
    rows = table.find_all(name='tr', class_=None)
    validate_table_header(rows[0])
    for row in rows[1:]:
        r = RowParser(row)
        yield pd.to_datetime(r.date), pd.to_numeric(r.value)


def make_df(parsed_rows):
    df = pd.DataFrame(data=parsed_rows,
                      columns=['CLOSE_DATE', 'DIVIDENDS'])
    return df.set_index('CLOSE_DATE').sort_index()


def get_dividends(ticker):
    url = make_url(ticker)
    doc = get_html(url)
    table = pick_table(doc)
    parsed_rows = parse_table_rows(table)
    return make_df(parsed_rows)


if __name__ == '__main__':
    print(get_dividends('CHMF'))
    # ВОПРОС: как эти данные дальше используются? склиеваются для одного 
    # эмитента разные показатели? или дивиденды по разным эмитентам?
    # если последнее - то в названии колонки надо выводить тикер 
    ticker = 'CHMF'
    url = make_url(ticker)
    doc = get_html(url)
    table = pick_table(doc)
    parsed_rows = parse_table_rows(table)
    df = make_df(parsed_rows)    
