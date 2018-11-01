"""Загружает дивиденды и даты закрытия с сайта www.dohod.ru"""

import urllib.error
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup

from web.labels import DATE

# Номер таблицы с дивидендами в документе
TABLE_INDEX = 2
# Позиции и наименования ключевых столбцов
TH_DATE = 'Дата закрытия реестра'
TH_VALUE = 'Дивиденд (руб.)'
DATE_COLUMN = 0
VALUE_COLUMN = 2


def make_url(ticker: str):
    """Формирует url - тикер необходимо перевести в маленькие буквы"""
    ticker = ticker.lower()
    return f'http://www.dohod.ru/ik/analytics/dividend/{ticker}'


def get_html(url: str):
    """Получает html"""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise urllib.error.URLError(f'Неверный url: {url}')
        else:
            raise error


def get_html_table(url: str, table_index: int):
    """Выбирает таблицу с дивидендами на странице"""
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')
    try:
        return soup.find_all('table')[table_index]
    except IndexError:
        raise IndexError(f'На странице {url} нет таблицы с дивидендами.')


class RowParserDohod:
    """Выбирает столбцы в ряду с датой закрытия реестра и дивидендами"""

    date_column = DATE_COLUMN
    value_column = VALUE_COLUMN

    def __init__(self, row: BeautifulSoup, is_header: bool = False):
        if is_header:
            column_html_tag = 'th'
        else:
            column_html_tag = 'td'
        self.columns = [column.text for column in row.find_all(column_html_tag)]

    @property
    def date(self):
        """Дата закрытия реестра"""
        return self.columns[self.date_column]

    @property
    def value(self):
        """Размер дивиденда"""
        return self.columns[self.value_column]


def validate_table_header(header: BeautifulSoup):
    """Проверка наименований столбцов с датой закрытия и дивидендами"""
    cells = RowParserDohod(header, True)
    if cells.date != TH_DATE or cells.value != TH_VALUE:
        raise ValueError('Некорректные заголовки таблицы дивидендов.')


def parse_table_rows(table: BeautifulSoup):
    """Строки с прогнозом имеют class = forecast, а у заголовка и факта - класс отсутствует"""
    rows = table.find_all(name='tr', class_=None)
    validate_table_header(rows[0])
    for row in rows[1:]:
        cells = RowParserDohod(row)
        yield pd.to_datetime(cells.date, dayfirst=True), pd.to_numeric(cells.value)


def make_df(ticker, parsed_rows):
    """Формирует DataFrame и упорядочивает даты по возрастанию"""
    df = pd.DataFrame(data=parsed_rows,
                      columns=[DATE, ticker])
    return df.set_index(DATE)[ticker].sort_index()


def dividends_dohod(ticker: str) -> pd.Series:
    """Возвращает Series с дивидендами упорядоченными по возрастанию даты закрытия реестра

    Parameters
    ----------
    ticker
        Тикер

    Returns
    -------
    pandas.Series
        Строки - даты закрытия реестра упорядоченные по возрастанию
        Значения - дивиденды
    """
    url = make_url(ticker)
    table = get_html_table(url, TABLE_INDEX)
    parsed_rows = parse_table_rows(table)
    return make_df(ticker, parsed_rows)


if __name__ == '__main__':
    print(dividends_dohod('SNGSP'))
