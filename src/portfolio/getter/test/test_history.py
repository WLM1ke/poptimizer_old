import pandas as pd

from portfolio.getter.history import get_quotes_history


def test_get_quotes_history():
    df = get_quotes_history('MSTT')
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 2
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('2010-11-03')
    assert df.shape[0] > 100
    assert df.loc['2018-03-09', 'CLOSE'] == 148.8
    assert df.loc['2018-03-09', 'VOLUME'] == 2960
