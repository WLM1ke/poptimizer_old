from pathlib import Path

import pytest

from portfolio import settings
from portfolio.getter import security_info


@pytest.fixture(scope='module', autouse=True)
def fake_data_path(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('data_get_tickers')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_first_get_tickers():
    assert security_info.get_reg_number_tickers(['UPRO']).loc['UPRO'] == 'UPRO EONR OGK4'


def test_download_tickers_for_get_tickers():
    assert security_info.get_reg_number_tickers(['TTLK']).loc['TTLK'] == 'TTLK'


def test_load_local_tickers_for_get_tickers():
    assert security_info.get_reg_number_tickers(['UPRO']).loc['UPRO'] == 'UPRO EONR OGK4'
