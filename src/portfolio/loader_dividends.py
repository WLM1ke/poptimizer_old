"""Dividends history downloader and parser."""

import urllib.request

import pandas as pd
from bs4 import BeautifulSoup


class Dividends:
    def __init__(self, ticker):
        self.ticker = ticker
        self._html = None

    @property
    def url(self):
        return f'http://www.dohod.ru/ik/analytics/dividend/{self.ticker.lower()}'

    @property
    def html(self):
        if self._html:
            return self._html
        else:
            # *requests* fails on SSL, using *urllib.request*
            with urllib.request.urlopen(self.url) as response:
                return response.read()

    @property
    def html_table(self):
        # TODO: как искать таблицу
        soup = BeautifulSoup(self.html, 'lxml')
        return soup.find_all('table')[2]

    @property
    def table_header(self):
        return self.html_table.find(name='tr').find_all(name='th')

    @property
    def columns_index(self):
        column_names = ['Дата закрытия реестра', 'Дивиденд (руб.)']
        return [i for i, column in enumerate(self.table_header) if column.string in column_names]

    @property
    def table_rows(self):
        # Строки с прогнозом имеют class = forecast
        return self.html_table.find_all(name='tr', class_=None)[1:]

    def yield_rows(self):
        for html_row in self.table_rows:
            row = [column.text.strip() for column in html_row.find_all('td')]
            try:
                yield dict(DATE=pd.to_datetime(row[0]), DIVIDEND=row[2])
            except (IndexError, ValueError):
                print("Not parsed:", row)

    @property
    def df(self):
        df = pd.DataFrame(columns=('DATE', 'DIVIDEND'))
        for row in self.yield_rows():
            df = df.append(row, ignore_index=True)
        return df.set_index('DATE')


if __name__ == '__main__':
    div = Dividends('CHMF')
    # print(div.columns_index)
    print(div.df)
