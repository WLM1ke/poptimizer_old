"""Загружает данные по предстоящим дивидендам с https://www.smart-lab.ru"""
import re

import pandas as pd
from bs4 import BeautifulSoup

from web.labels import TICKER, DATE, DIVIDENDS
from web.web_dividends_dohod import get_html_table, RowParserDohod

URL = 'https://smart-lab.ru/dividends/index/order_by_yield/desc/'
# Номер таблицы с дивидендами в документе
TABLE_INDEX = 2
# Позиции и наименования ключевых столбцов
TH_TICKER = 'Тикер'
TH_DATE = 'дата отсечки'
TH_VALUE = 'дивиденд,руб'
TICKER_COLUMN = 1
DATE_COLUMN = 4
VALUE_COLUMN = 7
DATE_PATTERN = '\d{2}\.\d{2}\.\d{4}'


class RowParserSmartLab(RowParserDohod):
    """Выбирает столбцы с тикером, датой закрытия реестра и дивидендами"""

    ticker_column = TICKER_COLUMN
    date_column = DATE_COLUMN
    value_column = VALUE_COLUMN

    @property
    def ticker(self):
        """Тикер"""
        return self.columns[self.ticker_column]


def validate_table_header(header: BeautifulSoup):
    """Проверка количества столбцов и наименований с тикером, датой закрытия и дивидендами"""
    columns_count = len(header.find_all('th'))
    if columns_count != 10:
        raise ValueError('Некорректное количество столбцов в заголовке таблицы дивидендов.')
    cells = RowParserSmartLab(header, True)
    if cells.ticker != TH_TICKER or cells.date != TH_DATE or cells.value != TH_VALUE:
        raise ValueError('Некорректные заголовки таблицы дивидендов.')


def validate_table_footer(footer: BeautifulSoup):
    """В последнем ряду должна быть одна ячейка"""
    columns_count = len(footer.find_all('td'))
    if columns_count != 1:
        raise ValueError('Некорректная последняя строка таблицы дивидендов.')


def parse_table_rows(table: BeautifulSoup):
    """Строки с прогнозом имеют class = dividend_approved"""
    rows = table.find_all(name='tr')
    validate_table_header(rows[0])
    validate_table_footer(rows[-1])
    for row in rows[1:-1]:
        if 'class' in row.attrs and 'dividend_approved' in row['class']:
            cells = RowParserSmartLab(row)
            yield (cells.ticker,
                   pd.to_datetime(re.search(DATE_PATTERN, cells.date).group(0), dayfirst=True),
                   pd.to_numeric(cells.value.replace(',', '.')))
        else:
            # Если появятся ячейки без класса утвержденных дивидендов, то надо разобраться с обработкой
            raise ValueError('Не утвержденные дивиденды')


def dividends_smart_lab():
    """
    Возвращает ожидаемые дивиденды с сайта https://smart-lab.ru/

    Returns
    -------
    pandas.DataFrame
        Строки - тикеры
        столбцы - даты закрытия и дивиденды
    """
    table = get_html_table(URL, TABLE_INDEX)
    parsed_rows = parse_table_rows(table)
    df = pd.DataFrame(data=parsed_rows,
                      columns=[TICKER, DATE, DIVIDENDS])
    return df.set_index(DATE)


if __name__ == '__main__':
    print(dividends_smart_lab())
