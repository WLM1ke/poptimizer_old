import datetime

import pandas as pd

from ..loader_index import make_url, get_index_history, get_raw_json


def test_make_url():
    url = make_url(datetime.date(2017, 10, 1), 50)
    assert url ==  ('http://iss.moex.com/iss/history/engines/stock/markets/index/'
                    'boards/RTSI/securities/MCFTRR.json?start=50&from=2017-10-01')    
    
def test_get_index_history():
    df = get_index_history(datetime.date(2017, 10, 2))
    assert isinstance(df, pd.DataFrame)
    assert df.index[0] == '2017-10-02'
    assert df.shape[0] > 100
    assert df.loc['2018-03-02', 'CLOSE'] == 3273.16


def test_get_raw_json_works_on_None_start_date():
    data = get_raw_json(start_date=None, block_position=0)
    index = data['history']['columns'].index('TRADEDATE')
    assert data['history']['data'][0][index] == '2003-02-26'
    

