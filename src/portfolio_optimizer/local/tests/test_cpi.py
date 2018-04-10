import time
from pathlib import Path

import pandas as pd
import pytest

from portfolio_optimizer import settings
from portfolio_optimizer.local import local_cpi
from portfolio_optimizer.settings import CPI


@pytest.fixture(scope='module', autouse=True)
def make_fake_path(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('cpi_test')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def check_results():
    df = local_cpi.get_cpi()
    assert isinstance(df, pd.Series)
    assert df.name == CPI
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('1991-01-31')
    assert df.shape[0] >= 326
    assert df.loc['2018-02-28'] == 1.0021


def test_get_cpi_create():
    check_results()


def test_get_cpi_need_update(monkeypatch):
    time.sleep(1)
    monkeypatch.setattr(local_cpi, 'UPDATE_PERIOD_IN_DAYS', 1 / (60 * 60 * 24))
    check_results()


def test_get_cpi_no_need_update():
    check_results()
