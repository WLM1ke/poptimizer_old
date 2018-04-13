from pathlib import Path

import arrow
import pandas as pd
import pytest

from portfolio_optimizer import settings
from portfolio_optimizer.local import data_manager
from portfolio_optimizer.local.data_manager import DataManager


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('data_manager')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def source_function():
    return pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})


def test_create():
    data = DataManager('test', 'test', source_function)
    assert not data._need_update()
    df = source_function()
    assert df.equals(data.get())


def test_update():
    data = DataManager('test', 'test', source_function)
    df = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
    assert df.equals(data.get())


def test_need_update(monkeypatch):
    patch_day = data_manager.END_OF_CURRENT_TRADING_DAY.shift(days=10)
    monkeypatch.setattr(data_manager, 'END_OF_CURRENT_TRADING_DAY', patch_day)
    data = DataManager('test', 'test', source_function)
    assert data._need_update()


def test_need_update(monkeypatch):
    patch_day = arrow.now()
    monkeypatch.setattr(data_manager, 'END_OF_CURRENT_TRADING_DAY', patch_day)
    data = DataManager('test', 'test', source_function)
    assert not data._need_update()
