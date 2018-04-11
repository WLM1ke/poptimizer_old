import pandas as pd
import pytest

from portfolio_optimizer.settings import COMPANY_NAME, REG_NUMBER, LOT_SIZE
from portfolio_optimizer.web.web_securities_info import make_url, get_json, securities_info


def test_make_url():
    assert make_url(('AKRN', 'GAZP', 'LKOH', 'SBER')).endswith('SBER')


@pytest.fixture(scope='class', name='json')
def make_json():
    return get_json(('AKRN', 'GAZP', 'LKOH', 'SBER'))


class TestGetRawJson:
    def test_get_raw_json_type(self, json):
        assert isinstance(json, dict)

    def test_get_raw_json_keys(self, json):
        assert list(json.keys()) == ['securities', 'marketdata', 'dataversion']


def test_get_securities_info():
    df = securities_info(('AKRN', 'GAZP', 'TTLK'))
    assert isinstance(df, pd.DataFrame)
    assert df.loc['AKRN', COMPANY_NAME] == 'Акрон'
    assert df.loc['GAZP', REG_NUMBER] == '1-02-00028-A'
    assert df.loc['TTLK', LOT_SIZE] == 10000


def test_one_security_info():
    df = securities_info(('MRSB',))
    assert isinstance(df, pd.DataFrame)
    assert df.loc['MRSB', COMPANY_NAME] == 'МордЭнСб'
    assert df.loc['MRSB', REG_NUMBER] == '1-01-55055-E'
    assert df.loc['MRSB', LOT_SIZE] == 10000
