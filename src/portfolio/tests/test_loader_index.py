import datetime

import pandas as pd

from ..loader_index import get_index_history


def test_get_index_history():
    df = get_index_history(datetime.date(2018, 2, 20))
    assert isinstance(df, pd.DataFrame)
    assert df.index[0] == '2018-02-20'
    assert df.loc['2018-03-02', 'CLOSE'] == 3273.16
