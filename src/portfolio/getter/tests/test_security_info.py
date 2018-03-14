from pathlib import Path

import pytest

from portfolio import settings
from portfolio.getter import security_info


@pytest.fixture(scope='module', autouse=True)
def fake_data_path(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('data')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_first_time_security_info():
    df = security_info.get_security_info(['KBTK', 'MOEX'])
    assert len(df.index) == 2
    assert len(security_info.load_securities_info().index) == 2


def test_second_time_security_info():
    df = security_info.get_security_info(['KBTK', 'MOEX'])
    assert len(df.index) == 2
    assert len(security_info.load_securities_info().index) == 2


def test_all_tickers_in_local_data_security_info():
    df = security_info.get_security_info(['MOEX'])
    assert len(df.index) == 1
    assert len(security_info.load_securities_info().index) == 2


def test_not_all_tickers_in_local_data_security_info():
    df = security_info.get_security_info(['MOEX', 'MTSS'])
    assert len(df.index) == 2
    assert len(security_info.load_securities_info().index) == 3


def test_all_tickers_are_new_time_security_info():
    df = security_info.get_security_info(['SNGSP', 'GAZP'])
    assert len(df.index) == 2
    df_local = security_info.load_securities_info()
    assert len(df_local.index) == 5
    assert df.equals(df_local.loc[['SNGSP', 'GAZP']])
    assert df_local.loc['KBTK', 'SHORTNAME'] == 'КузбТК ао'
    assert df_local.loc['MOEX', 'REGNUMBER'] == '1-05-08443-H'
    assert df.loc['SNGSP', 'LOTSIZE'] == 100
