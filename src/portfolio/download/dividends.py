"""Download and transform dividends data to pandas DataFrames.

    Single ticker close dates and dividends:

        get_ticker_dividends(ticker)
"""

import urllib.error
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup

# Номер таблицы с дивидендами
TABLE_INDEX = 2
# Позиции, наименования ключевых столбцов и их имя в DataFrame
HEADER = [(0, 'Дата закрытия реестра'),
          (2, 'Дивиденд (руб.)')]


def make_url(ticker):
    # Обычно тикеры пишутся всеми большими буквами, но в url они должны быть маленькими
    return f'http://www.dohod.ru/ik/analytics/dividend/{ticker.lower()}'


def validate_table_header(header):
    header_names = [column.string for column in header.find_all(name='th')]
    if any(header_names[i] != name for i, name in HEADER):
        raise ValueError('Некоректные заголовки таблицы дивидендов.')


def parse_table_rows(html_table):
    # Строки с прогнозом имеют class = forecast, а у заголовка и факта - класс отсутсвует
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
    try:
        # *requests* fails on SSL, using *urllib.request*
        with urllib.request.urlopen(url) as response:
            soup = BeautifulSoup(response.read(), 'lxml')
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise urllib.error.URLError(f'Неверный url: {url}')
        else:
            raise error
    html_table = soup.find_all('table')[TABLE_INDEX]
    parsed_rows = parse_table_rows(html_table)
    return make_df(parsed_rows)


if __name__ == '__main__':
    print(get_dividends('CHMF'))
