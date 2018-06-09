import pandas as pd

from portfolio_optimizer.local.local_dividends_dohod import dividends


def test_dividends():
    df = dividends('GAZP')
    assert isinstance(df, pd.Series)
    assert df.name == 'GAZP'
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.loc['2003-02-21'] == 0.4
    assert df.loc['2017-07-20'] == 8.04
