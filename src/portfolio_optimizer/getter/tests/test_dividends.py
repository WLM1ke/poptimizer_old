import time
from pathlib import Path

import pytest

from portfolio_optimizer import settings
from portfolio_optimizer.getter import local_dividends


@pytest.fixture(scope='module', autouse=True)
def security_data_path(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('new_dividends')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_get_dividends_first_time():
    df = local_dividends.get_dividends(['GAZP', 'MRKC'])
    assert len(df.columns) == 2
    assert df.index.is_monotonic_increasing
    assert df.index.unique
    assert df.loc['2002-05-13', 'GAZP'] == 0.44
    assert df.loc['2017-06-21', 'MRKC'] == 0.0442


def test_forced_update_fake_new_rows(monkeypatch):
    dividends_object = local_dividends.LocalDividends('GAZP')
    dividends_object.df = dividends_object.df.reindex(dividends_object.df.index[:-1])
    monkeypatch.setattr(local_dividends, 'UPDATE_PERIOD_IN_DAYS', 1 / (60 * 60 * 24))
    time.sleep(1)
    dividends_object.update_local_history()
    df = dividends_object.df
    assert df.index.is_monotonic_increasing
    assert df.index.unique
    assert df.loc['2002-05-13'] == 0.44
    assert df.loc['2017-07-20'] == 8.04


def test_forced_update_now_new_rows(monkeypatch):
    monkeypatch.setattr(local_dividends, 'UPDATE_PERIOD_IN_DAYS', 1 / (60 * 60 * 24))
    time.sleep(1)
    test_get_dividends_first_time()


def test_get_dividends_no_update():
    test_get_dividends_first_time()
