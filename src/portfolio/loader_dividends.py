"""Dividends history downloader and parser."""

import urllib.request

import pandas as pd
from bs4 import BeautifulSoup


def get_text(url):
    # *requests* fails on SSL, using *urllib.request*
    with urllib.request.urlopen(url) as response:
        return response.read()


def yield_rows(table: str):
    for html_row in table.find_all('tr'):
        row = [column.text.strip() for column in html_row.find_all('td')]
        try:
            yield dict(DATE=pd.to_datetime(row[0]), DIVIDEND=row[2])
        except (IndexError, ValueError) as e:
            print("Not parsed:", row)


def make_dataframe(table: str):
    df = pd.DataFrame(columns=('DATE', 'DIVIDEND'))
    for row in yield_rows(table):
        df = df.append(row, ignore_index=True)
    return df.set_index('DATE').drop_duplicates()


def make_url(ticker):
    return f'http://www.dohod.ru/ik/analytics/dividend/{ticker.lower()}'

if __name__ == '__main__':
    html = get_text(make_url('CHMF'))
    # identify table
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find_all('table')[2]
    df = make_dataframe(table)
    print(df)
