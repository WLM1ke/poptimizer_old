import pandas as pd
import pytest

from web import moex
from web.labels import CLOSE_PRICE, VOLUME


def test_quotes_t2():
    df = moex.quotes_t2('LSNGP')
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == [CLOSE_PRICE, VOLUME]
    assert df.index[0] == pd.Timestamp('2014-06-09')
    assert df.loc['2014-06-09', CLOSE_PRICE] == pytest.approx(14.7)
    assert df.loc['2014-10-28', VOLUME] == 87600
    assert df.loc['2018-09-07', CLOSE_PRICE] == pytest.approx(86.5)
    assert df.loc['2018-05-31', VOLUME] == 216300


def test_quotes_t2_with_start():
    df = moex.quotes_t2('LSRG', pd.Timestamp('2018-08-07'))
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == [CLOSE_PRICE, VOLUME]
    assert df.index[0] == pd.Timestamp('2018-08-07')
    assert df.loc['2018-08-07', CLOSE_PRICE] == pytest.approx(777)
    assert df.loc['2018-08-10', VOLUME] == 11313
    assert df.loc['2018-09-06', CLOSE_PRICE] == pytest.approx(660)
    assert df.loc['2018-08-28', VOLUME] == 47428
