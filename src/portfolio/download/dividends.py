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
# позиции, наименования ключевых столбцов и их имя в DataFrame
HEADER = [(0, 'Дата закрытия реестра'),
          (2, 'Дивиденд (руб.)')]


def get_html(url):
    try:
        # *requests* fails on SSL, using *urllib.request*
        with urllib.request.urlopen(url) as response:
            # EP: это плохо тестируется и перескакивает между уровнями
            # return BeautifulSoup(response.read(), 'lxml')
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise urllib.error.URLError(f'Неверный url: {url}')
        else:
            raise error


def make_url(ticker):
    # Обычно тикеры пишутся всеми большими буквами, но в url они должны быть маленькими
    ticker = ticker.lower()
    return f'http://www.dohod.ru/ik/analytics/dividend/{ticker}'


def pick_table(html: str, n: int=TABLE_INDEX):
    soup = BeautifulSoup(html, 'lxml')
    return soup.find_all('table')[n]


def parse_table_rows(html_table):
    # Строки с прогнозом имеют class = forecast, а у заголовка и факта 
    # - класс отсутсвует
    def validate_table_header(header):
        header_names = [column.string for column in header.find_all(name='th')]
        if any(header_names[i] != name for i, name in HEADER):
            raise ValueError('Некоректные заголовки таблицы дивидендов.')
    rows = html_table.find_all(name='tr', class_=None)
    validate_table_header(rows[0])
    data = []
    for row in rows[1:]:
        row = [column.string for column in row.find_all('td')]
        data.append([pd.to_datetime(row[HEADER[0][0]]),
                     pd.to_numeric(row[HEADER[1][0]])])
    return data


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
    
