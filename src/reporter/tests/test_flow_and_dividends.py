from pathlib import Path

import pandas as pd
import pytest

from reporter.flow_and_dividends import make_12m_dividends_df, make_list_of_lists_dividends
from reporter.flow_and_dividends import make_flow_df, make_list_of_lists_flow


def read_test_df():
    return pd.read_excel(Path(__file__).parent / 'data' / 'test.xlsx',
                         sheet_name='Data',
                         header=0,
                         index_col=0,
                         converters={'Date': pd.to_datetime})[-63:-2]


def test_make_flow_df():
    df = make_flow_df(read_test_df())
    assert df.shape == (7, 3)
    assert df.loc['2018-01-19', 'WLMike'] == pytest.approx(384887.052476377)
    assert df.iat[1, 1] == pytest.approx(0.0258042361251882)
    assert df.loc['Pre Inflow', 'Portfolio'] == pytest.approx(394913.2498)
    assert df.iat[3, 0] == pytest.approx(0.974195763874812)
    assert df.loc['Inflow', 'WLMike'] == pytest.approx(1091.60460000001)
    assert df.loc['2018-02-19', 'Igor'] == pytest.approx(10190.4347468046)
    assert df.iat[-1, -1] == pytest.approx(1)


def test_make_list_of_lists_flow():
    list_of_lists = make_list_of_lists_flow(read_test_df())
    assert len(list_of_lists) == 8
    assert list_of_lists[0] == ['', 'WLMike', 'Igor', 'Portfolio']
    assert list_of_lists[1] == ['2018-01-19', '384 887', '10 195', '395 082']
    assert list_of_lists[2] == ['%', '97.42%', '2.58%', '100.00%']
    assert list_of_lists[3] == ['Pre Inflow', '384 723', '10 190', '394 913']
    assert list_of_lists[4] == ['%', '97.42%', '2.58%', '100.00%']
    assert list_of_lists[5] == ['Inflow', '1 092', '0', '1 092']
    assert list_of_lists[6] == ['2018-02-19', '385 814', '10 190', '396 005']
    assert list_of_lists[7] == ['%', '97.43%', '2.57%', '100.00%']


def test_make_12m_dividends_df():
    df = make_12m_dividends_df(read_test_df())
    assert df.iloc[-1] == pytest.approx(28948.1439)
    assert df.iloc[-27] == pytest.approx(11919.4743)
    assert df.iloc[-29] == pytest.approx(11609.3758)


def test_make_list_of_lists_dividends():
    list_of_lists = make_list_of_lists_dividends(read_test_df())
    assert len(list_of_lists) == 7
    assert list_of_lists[0] == ['Period', 'Dividends']
    assert list_of_lists[1] == ['2018-01-19 - 2018-02-19', '999']
    assert list_of_lists[2] == ['2017-02-17 - 2018-02-19', '28 948']
    assert list_of_lists[-1] == ['2013-02-19 - 2014-02-19', '3 865']
