import pandas as pd

from web.labels import CLOSE_PRICE
from web.web_index import index, Index


def test_index_none_start_date():
    index_gen = Index(None)
    assert index_gen.url == ('http://iss.moex.com/iss/history/engines/stock/markets/index/'
                             'boards/RTSI/securities/MCFTRR.json?start=0')
    assert index_gen.df.index[0] == pd.Timestamp('2003-02-26')
    assert len(index_gen) == 100
    assert index_gen.df.loc['2003-02-26', CLOSE_PRICE] == 335.67
    assert list(index_gen.df.columns) == [CLOSE_PRICE]


def test_index_is_iterable():
    index_gen = Index(pd.to_datetime('2017-10-01'))
    assert index_gen.url == ('http://iss.moex.com/iss/history/engines/stock/markets/index/'
                             'boards/RTSI/securities/MCFTRR.json?start=0&from=2017-10-01')
    assert len(list(index_gen)) >= 2


def test_index():
    df = index(pd.to_datetime('2017-10-02'))
    assert isinstance(df, pd.Series)
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('2017-10-02')
    assert df.shape[0] >= 100
    assert df.loc['2018-03-02'] == 3273.16
