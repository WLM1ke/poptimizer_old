from pathlib import Path

import arrow
import pandas as pd
import pytest

import settings
from local.dividends import dohod_ru


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('test_local_dividends_dohod')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_dividends():
    df = dohod_ru.dividends_dohod('GAZP')
    assert isinstance(df, pd.Series)
    assert df.name == 'GAZP'
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.loc['2003-02-21'] == 0.4
    assert df.loc['2017-07-20'] == 8.04


def test_update():
    time0 = arrow.now()
    manager = dohod_ru.DohodDataManager('LKOH')
    assert manager.last_update > time0
    df = manager.value
    time1 = arrow.now()
    assert manager.last_update < time1
    manager.update()
    assert manager.last_update > time1
    assert df.equals(manager.value)
