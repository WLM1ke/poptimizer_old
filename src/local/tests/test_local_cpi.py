import pandas as pd

from local import local_cpi
from web.labels import CPI


def test_cpi():
    df = local_cpi.cpi()
    assert isinstance(df, pd.Series)
    assert df.name == CPI
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('1991-01-31')
    assert df.shape[0] >= 326
    assert df.loc['2018-02-28'] == 1.0021
