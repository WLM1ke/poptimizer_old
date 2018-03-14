"""Downloader and parser for CPI."""

from datetime import date

import pandas as pd

URL_CPI = 'http://www.gks.ru/free_doc/new_site/prices/potr/I_ipc.xlsx'
PARSING_PARAMETERS = dict(sheet_name='ИПЦ', header=3, skiprows=[4], skip_footer=3)


def validate(df):
    months, _ = df.shape
    first_year = df.columns[0]
    first_month = df.index[0]
    if months != 12:
        raise ValueError('Data must contain 12 rows only')
    if first_year != 1991:
        raise ValueError('First year must be 1991')
    if first_month != 'январь':
        raise ValueError('First month must be January')


def parse_xls(url) -> pd.DataFrame:
    df = pd.read_excel(url, **PARSING_PARAMETERS)
    validate(df)
    size = df.shape[0] * df.shape[1]
    first_year = df.columns[0]
    # create new DataFrame
    index = pd.DatetimeIndex(name="DATE", freq='M', start=date(first_year, 1, 31), periods=size)
    flat_data = df.values.reshape(size, order='F')
    df = pd.DataFrame(flat_data, index=index, columns=['CPI']).dropna()
    return df.div(100)


def get_monthly_cpi():
    return parse_xls(URL_CPI)


if __name__ == '__main__':
    print(get_monthly_cpi())
