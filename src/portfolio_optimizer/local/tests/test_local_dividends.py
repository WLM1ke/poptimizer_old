import pandas as pd

from portfolio_optimizer.local import local_dividends


def test_dividends():
    df = local_dividends.dividends('GAZP')
    assert isinstance(df, pd.Series)
    assert df.name == 'GAZP'
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.loc['2002-05-13'] == 0.44
    assert df.loc['2017-07-20'] == 8.04
