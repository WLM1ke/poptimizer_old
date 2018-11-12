"""Загружает дивиденды и даты закрытия с сайта www.dohod.ru"""
import ssl
import urllib.error
import urllib.request

import pandas as pd

from web.dividends import parser
from web.labels import DATE

TABLE_INDEX = 2
HEADER_SIZE = 1

DATE_COLUMN = parser.DataColumn(0,
                                {0: 'Дата закрытия реестра'},
                                parser.date_parser)

DIVIDENDS_COLUMN = parser.DataColumn(2,
                                     {0: 'Дивиденд (руб.)'},
                                     parser.div_parser)


def make_url(ticker: str):
    """Формирует url - тикер необходимо перевести в маленькие буквы"""
    ticker = ticker.lower()
    return f'http://www.dohod.ru/ik/analytics/dividend/{ticker}'


def get_html(url: str):
    """Получает html-код для url"""
    try:
        with urllib.request.urlopen(url, context=ssl.SSLContext()) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise urllib.error.URLError(f'Неверный url: {url}')
        else:
            raise


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
    html = get_html(url)
    table = parser.HTMLTableParser(html, TABLE_INDEX)
    columns = [DATE_COLUMN, DIVIDENDS_COLUMN]
    df = table.make_df(columns, HEADER_SIZE)
    df.columns = [DATE, ticker]
    df.set_index(DATE, inplace=True)
    df.sort_index(inplace=True)
    return df[ticker]


if __name__ == '__main__':
    print(dividends_dohod('AKRN'))
