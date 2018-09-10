from pathlib import Path

import arrow
import pandas as pd
import pytest

import settings
from local.dividends import smart_lab_ru
from local.dividends.smart_lab_ru import SmartLabDataManager
from web import dividends


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('test_local_dividends_smart_lab')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_dividends_smart_lab():
    df = smart_lab_ru.dividends_smart_lab()
    assert df.equals(dividends.smart_lab())


def test_update():
    manager = SmartLabDataManager()
    time0 = arrow.now()
    assert manager.last_update < time0
    manager.update()
    assert time0 < manager.last_update


def test_download_update():
    with pytest.raises(NotImplementedError):
        manager = SmartLabDataManager()
        manager.download_update()


def test_dividends_smart_lab_for_ticker():
    df = smart_lab_ru.dividends_smart_lab('CHMF')
    assert isinstance(df, pd.Series)
    assert df.name == 'CHMF'
