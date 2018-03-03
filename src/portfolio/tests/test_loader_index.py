import datetime

import pandas as pd

from ..loader_index import get_index_history, get_raw_json


def test_get_index_history():
    df = get_index_history(datetime.date(2017, 10, 2))
    assert isinstance(df, pd.DataFrame)
    assert df.index[0] == '2017-10-02'
    assert df.shape[0] > 100
    assert df.loc['2018-03-02', 'CLOSE'] == 3273.16


def test_get_raw_json():
    data = get_raw_json(None, 0)
    index = data['history']['columns'].index('TRADEDATE')
    assert data['history']['data'][0][index] == '2003-02-26'
