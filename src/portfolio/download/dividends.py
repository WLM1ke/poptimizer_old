"""Download and transform dividends data to pandas DataFrames.

   Single ticker close dates and dividends:

       get_dividends(ticker)
"""

import urllib.error
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup

# Номер таблицы с дивидендами в документе
TABLE_INDEX = 2
# Позиции и наименования ключевых столбцов
TH_DATE = 'Дата закрытия реестра'
TH_VALUE = 'Дивиденд (руб.)'
DATE_COLN = 0
VALUE_COLN = 2


def make_url(ticker: str):
    """Формирует url - тикер необходимо перевести в маленькие буквы."""
    ticker = ticker.lower()
    return f'http://www.dohod.ru/ik/analytics/dividend/{ticker}'


def get_html(url):
    """Получает html - *requests* fails on SSL, using *urllib.request."""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise urllib.error.URLError(f'Неверный url: {url}')
        else:
            raise error


def pick_table(html: str, n: int = TABLE_INDEX):
    """Выбирает таблицу с дивидендами на странице."""
    soup = BeautifulSoup(html, 'lxml')
    return soup.find_all('table')[n]


class RowParser:
    """Выбирает ячейки в ряду с датой закрытия реестра и дивидендами."""
    def __init__(self, row, tag='td'):
        self.columns = [column.string for column in row.find_all(tag)]

    @property
    def date(self):
        """Дата закрытия реестра"""
        return self.columns[DATE_COLN]  # 0

    @property
    def value(self):
        """Размер дивиденда"""
        return self.columns[VALUE_COLN]  # 2


def validate_table_header(header):
    """Проверка наименований столбцов с датой закрытия и дивидендами."""
    cells = RowParser(header, 'th')
    if cells.date != TH_DATE or cells.value != TH_VALUE:
        raise ValueError('Некоректные заголовки таблицы дивидендов.')


def parse_table_rows(table):
    """Строки с прогнозом имеют class = forecast, а у заголовка и факта - класс отсутсвует."""
    rows = table.find_all(name='tr', class_=None)
    validate_table_header(rows[0])
    for row in rows[1:]:
        cells = RowParser(row)
        yield pd.to_datetime(cells.date), pd.to_numeric(cells.value)


def make_df(parsed_rows):
    """Формирует DataFrame и упорядычивает даты по возростанию."""
    df = pd.DataFrame(data=parsed_rows,
                      columns=['CLOSE_DATE', 'DIVIDENDS'])
    return df.set_index('CLOSE_DATE')['DIVIDENDS'].sort_index()


def get_dividends(ticker: str) -> pd.Series:
    """
    Возвращает Series с двивидендами упорядоченными по возростанию даты закрытия реестра.

    Parameters
    ----------
    ticker
        Тикер.

    Returns
    -------
    pandas.Series
        Строки - даты закрытия реестраб упорядоченные по возрастанию.
        Значения - дивиденды.
    """
    url = make_url(ticker)
    html = get_html(url)
    table = pick_table(html)
    parsed_rows = parse_table_rows(table)
    return make_df(parsed_rows)


if __name__ == '__main__':
    print(get_dividends('CHMF'))
