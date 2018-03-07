import datetime

import pandas as pd

from ..loader_history import get_ticker_history, make_url, get_index_history, get_json, TotalReturn, Ticker


def test_make_url():
    url = make_url(base=TotalReturn.base,
                   ticker=TotalReturn.ticker,
                   start_date=datetime.date(2017, 10, 1),
                   block_position=50)
    assert url == ('http://iss.moex.com/iss/history/engines/stock/markets/index/'
                   'boards/RTSI/securities/MCFTRR.json?start=50&from=2017-10-01')


def test_make_url_defaults():
    url = make_url(base=Ticker.base + '/',
                   ticker='AKRN')
    assert url == ('https://iss.moex.com/iss/history/engines/stock/markets'
                   '/shares/securities/AKRN.json?start=0')


def test_get_raw_json_works_on_none_start_date():
    url = make_url(base=TotalReturn.base,
                   ticker=TotalReturn.ticker)
    data = get_json(url)
    index = data['history']['columns'].index('TRADEDATE')
    assert data['history']['data'][0][index] == '2003-02-26'


def test_get_index_history():
    df = get_index_history(datetime.date(2017, 10, 2))
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 1
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == '2017-10-02'
    assert df.shape[0] >= 100
    assert df.loc['2018-03-02', 'CLOSE'] == 3273.16


def test_get_ticker_history_from_start():
    df = get_ticker_history('MOEX', datetime.date(2017, 10, 2))
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 2
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == '2017-10-02'
    assert df.shape[0] > 100
    assert df.loc['2018-03-05', 'CLOSE'] == 117
    assert df.loc['2018-03-05', 'VOLUME'] == 4553310


def test_ticker_is_iterable(): 
    t = Ticker('AKRN', datetime.date(2017, 3, 1))
    assert len(list(t)) >= 3


class TestTotalReturn:
    def test_dataframe(self):
        index_quotes = TotalReturn(None)
        assert isinstance(index_quotes.dataframe, pd.DataFrame)
        assert index_quotes.dataframe.loc['2003-02-26', 'CLOSE'] == 335.67
