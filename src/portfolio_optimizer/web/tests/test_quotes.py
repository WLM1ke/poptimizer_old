import pandas as pd

from portfolio_optimizer.web.labels import CLOSE_PRICE, DATE, VOLUME
from portfolio_optimizer.web.web_quotes import quotes, Quotes


def test_quotes_none_start_date():
    quotes_gen = Quotes('AKRN', None)
    assert quotes_gen.url == ('https://iss.moex.com/iss/history/engines/stock/markets'
                              '/shares/securities/AKRN.json?start=0')
    assert quotes_gen.df.loc[0, DATE] == pd.Timestamp('2006-10-11')


def test_quotes_is_iterable():
    quotes_gen = Quotes('AKRN', pd.Timestamp('2017-03-01'))
    assert quotes_gen.df.loc[0, DATE] == pd.Timestamp('2017-03-01')
    assert len(list(quotes_gen)) >= 3


def test_quotes():
    df = quotes('MOEX', pd.Timestamp('2017-10-02'))
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 2
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.Timestamp('2017-10-02')
    assert df.shape[0] > 100
    assert df.loc['2018-03-05', CLOSE_PRICE] == 117
    assert df.loc['2018-03-05', VOLUME] == 4553310
