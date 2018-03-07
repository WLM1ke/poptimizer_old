"""Dividends history downloader and parser."""

import urllib.request
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


def get_text(url):
    # *requests* fails on SSL, using *urllib.request*
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


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
    return (df.set_index('DATE'))


if __name__ == '__main__':
    url = 'http://www.dohod.ru/ik/analytics/dividend/rtkmp'
    # dirty cache
    cache = Path('temp.txt')
    if cache.exists():
        html = cache.read_text()
    else:
        html = get_text(url)
        cache.write_text(html)
        # identify table
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find_all('table')[2]
    df = make_dataframe(table)
    print(df)

header = soup.find(name='th', text='Дата закрытия реестра').parent

for n, column in enumerate(header.findall(name='th')):
    if column.string in {'Дата закрытия реестра', 'Дивиденд (руб.)'}:
        print(n)
