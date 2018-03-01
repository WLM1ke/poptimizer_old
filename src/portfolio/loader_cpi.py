"""Downloader and parser for CPI."""

import pandas as pd
import requests
from datetime import date
# requires python 3.6
from pathlib import Path

def find_root():
    """Return path to repo root."""
    return Path(__file__).parents[2]

def make_path(subfolder, filename):
    folder = find_root() / 'data' / subfolder 
    if not folder.exists():
        folder.mkdir(parents=True)
    return str(folder / filename)

def make_path_raw(filename):
    return make_path('raw', filename)

def make_path_parsed(filename):
    return make_path('parsed', filename)


URL_CPI = 'http://www.gks.ru/free_doc/new_site/prices/potr/I_ipc.xlsx'
PATH_RAW_CPI = make_path_raw('I_ipc.xlsx')
PATH_PARSED_CPI = make_path_parsed('cpi.txt')
    
def download(url, local_path):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(local_path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
    else:
        # FIXME: better exception?
        raise Exception("No connection - file fron internet not loaded")               
# TODO test: write file to temp destination and assert it exists    

def parse_local_dataframe_cpi(path=PATH_RAW_CPI):        
    if not Path(path).exists():
        raise FileNotFoundError(path)
    df = pd.read_excel(path, sheet_name='ИПЦ', header=3, skiprows=[4], skip_footer=3)
    months, years = df.shape
    year = df.columns[0] 
    size = months * years    
    # EP: more readable 'if' clauses + error messages in English (better)
    if months != 12:
        raise ValueError('Data must contain 12 rows only')
    if df.columns[0] != 1991:
        raise ValueError('First year must be 1991')
    if df.index[0] != 'январь':
        raise ValueError('First month must be January')
    # create new dataframe
    index = pd.DatetimeIndex(freq='M', start=date(year, 1, 31), periods=size)
    flat_data = df.values.reshape(months * years, order='F')
    return pd.DataFrame(flat_data, index=index, columns=['CPI']).dropna() / 100# TODO test: make sure data includes checkpoints 


def read_df(source):
    converter_arg = dict(converters={0: pd.to_datetime}, index_col=0)
    return pd.read_csv(source, **converter_arg)

def update_from_web_cpi():
    download(URL_CPI, PATH_RAW_CPI)
    df_cpi = parse_local_dataframe_cpi()
    path = make_path_parsed(PATH_PARSED_CPI)
    #FIXME: maybe round to 4 digits?
    # df_cpi.loc['2017-09-30',][0]
    # Out[16]: 0.9984999999999999
    df_cpi.to_csv(path)
    return df_cpi    

def monthly_cpi():
    return read_df(PATH_PARSED_CPI)    

if __name__ == '__main__':
    df1 = update_from_web_cpi()
    df2 = monthly_cpi()
    for df in [df1, df2]:
        assert df.CPI.loc['2018-01-31'] == 1.0031    
        assert df.CPI.loc['1991-01-31'] == 1.0620   
        
    print(df1.head())
    print(df2.tail())
    assert (df1.CPI.round(4) == df2.CPI.round(4)).all()
