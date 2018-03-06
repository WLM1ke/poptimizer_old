import datetime

import pandas as pd

from ..loader_history import compose_ticker_url_function, get_ticker_history
from ..loader_history import index_url, get_index_history, TotalReturn


def test_make_url():
    url = index_url(datetime.date(2017, 10, 1), 50)
    assert url == ('http://iss.moex.com/iss/history/engines/stock/markets/index/'
                   'boards/RTSI/securities/MCFTRR.json?start=50&from=2017-10-01')


def test_get_raw_json_works_on_none_start_date():
    data = TotalReturn.get_raw_json(index_url, start_date=None, block_position=0)
    index = data['history']['columns'].index('TRADEDATE')
    assert data['history']['data'][0][index] == '2003-02-26'


def test_get_index_history():
    df = get_index_history(datetime.date(2017, 10, 2))
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 1
    assert df.index[0] == '2017-10-02'
    assert df.shape[0] > 100
    assert df.loc['2018-03-02', 'CLOSE'] == 3273.16


def test_compose_ticker_url_function():
    url_function = compose_ticker_url_function('AKRN')
    assert url_function(datetime.date(2017, 10, 2), 100) == ('https://iss.moex.com/iss/history/engines/stock/markets'
                                                             '/shares/securities/AKRN.json?start=100&from=2017-10-02')


def test_get_ticker_history_from_start():
    df = get_ticker_history('MOEX', datetime.date(2017, 10, 2))
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 2
    assert df.index[0] == '2017-10-02'
    assert df.shape[0] > 100
    assert df.loc['2018-03-05', 'CLOSE'] == 117
    assert df.loc['2018-03-05', 'VOLUME'] == 4553310
