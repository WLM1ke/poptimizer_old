import pandas as pd

from portfolio_optimizer.local import local_index
from portfolio_optimizer.settings import CLOSE_PRICE


def test_index():
    df = local_index.index()
    assert isinstance(df, pd.Series)
    assert df.name == CLOSE_PRICE
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('2003-02-26')
    assert df.shape[0] > 100
    assert df.loc['2018-03-16'] == 3281.58
