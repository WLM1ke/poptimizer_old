from pathlib import Path

import pandas as pd
import pytest

import settings
from local import local_dividends_dohod


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('test_local_dividends_dohod')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_dividends():
    df = local_dividends_dohod.dividends('GAZP')
    assert isinstance(df, pd.Series)
    assert df.name == 'GAZP'
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.loc['2003-02-21'] == 0.4
    assert df.loc['2017-07-20'] == 8.04


def test_need_update_false():
    manager = local_dividends_dohod.DividendsDohodDataManager('GAZP')
    assert not manager._need_update()


def test_need_update_true(monkeypatch):
    monkeypatch.setattr(local_dividends_dohod, 'DAYS_TO_UPDATE', 0)
    manager = local_dividends_dohod.DividendsDohodDataManager('GAZP')
    assert manager._need_update()
