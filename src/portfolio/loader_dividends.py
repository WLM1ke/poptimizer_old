"""Dividends history downloader and parser."""

import urllib.error
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup


class Dividends:
    table_index = 2
    date_index = 0
    date_name = 'Дата закрытия реестра'
    dividend_index = 2
    dividend_name = 'Дивиденд (руб.)'

    def __init__(self, ticker):
        self.ticker = ticker
        self._html = None

    @property
    def url(self):
        return f'http://www.dohod.ru/ik/analytics/dividend/{self.ticker.lower()}'

    @property
    def html(self):
        # Запоминается значение, чтобы не дергать url повторно
        if self._html:
            return self._html
        else:
            try:
                # *requests* fails on SSL, using *urllib.request*
                with urllib.request.urlopen(self.url) as response:
                    self._html = response.read()
                    return self._html
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    raise urllib.error.URLError(f'Не верный url: {self.url}')

    @property
    def html_table(self):
        soup = BeautifulSoup(self.html, 'lxml')
        return soup.find_all('table')[self.table_index]

    def _validate_table_header(self):
        names = [column.string for column in self.html_table.find(name='tr').find_all(name='th')]
        if names[self.date_index] != self.date_name or names[self.dividend_index] != self.dividend_name:
            raise ValueError(f'Не коректные заголовки таблицы дивидендов {self.ticker}')

    @property
    def table_rows(self):
        self._validate_table_header()
        # Строки с прогнозом имеют class = forecast
        return self.html_table.find_all(name='tr', class_=None)[1:]

    def _yield_rows(self):
        for html_row in self.table_rows:
            row = [column.string for column in html_row.find_all('td')]
            yield pd.DataFrame(data=[row[self.dividend_index]],
                               columns=['DIVIDENDS'],
                               index=[row[self.date_index]])

    @property
    def df(self):
        df = pd.concat(self._yield_rows())
        df.index = pd.to_datetime(df.index)
        return df.sort_index()


def get_ticker_dividends(ticker):
    return Dividends(ticker).df


if __name__ == '__main__':
    div = Dividends('CHMF')
    print(div.df)
