import datetime

import pandas as pd

from portfolio.download.history import get_quotes_history, make_url, get_index_history, get_json, TotalReturn, Quotes


def test_make_url():
    url = make_url(base=TotalReturn.base,
                   ticker=TotalReturn.ticker,
                   start_date=datetime.date(2017, 10, 1),
                   block_position=50)
    assert url == ('http://iss.moex.com/iss/history/engines/stock/markets/index/'
                   'boards/RTSI/securities/MCFTRR.json?start=50&from=2017-10-01')


def test_make_url_defaults():
    url = make_url(base=Quotes.base + '/',
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


def test_get_quotes_history():
    df = get_quotes_history('MOEX', datetime.date(2017, 10, 2))
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 2
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == '2017-10-02'
    assert df.shape[0] > 100
    assert df.loc['2018-03-05', 'CLOSE'] == 117
    assert df.loc['2018-03-05', 'VOLUME'] == 4553310


class TestTicker:
    def test_ticker_is_iterable(self):
        t = Quotes('AKRN', datetime.date(2017, 3, 1))
        assert len(list(t)) >= 3


class TestTotalReturn:
    t = TotalReturn(start_date=None)
    
    def test_data_property_on_init_for_None_start_date(self):
        # lower-level test of server response
        data = self.t.data
        index = data['history']['columns'].index('TRADEDATE')
        assert data['history']['data'][0][index] == '2003-02-26'
        
    def test_len_method(self):
        assert len(self.t) == 100        
    
    def test_bool_method(self):
        assert bool(self.t)
        
    def test_values_property(self):
        assert isinstance(self.t.values, list)
        assert len(self.t.values[0]) == 16

    def test_columns_property(self):
        assert self.t.columns == ['BOARDID',
             'SECID',
             'TRADEDATE',
             'SHORTNAME',
             'NAME',
             'CLOSE',
             'OPEN',
             'HIGH',
             'LOW',
             'VALUE',
             'DURATION',
             'YIELD',
             'DECIMALS',
             'CAPITALIZATION',
             'CURRENCYID',
             'DIVISOR']

    def test_dataframe_property(self):
        assert isinstance(self.t.dataframe, pd.DataFrame)        
        assert list(self.t.dataframe.columns) == ['CLOSE']
        assert self.t.dataframe.loc['2003-02-26', 'CLOSE'] == 335.67
