import time
from os import path
from pathlib import Path

import pandas as pd
import pytest

from optimizer import settings
from optimizer.getter import local_cpi
from optimizer.getter.local_cpi import get_cpi, load_cpi, validate, cpi_path, update_cpi
from optimizer.settings import CPI


@pytest.fixture(scope='module', name='dfs', autouse=True)
def make_test_path_and_dfs(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('cpi_test')
    settings.DATA_PATH = Path(temp_dir)
    dfs = [get_cpi(), get_cpi()]
    yield dfs
    settings.DATA_PATH = saved_path


@pytest.fixture(params=range(2), name='df')
def yield_df(request, dfs):
    return dfs[request.param]


def test_get_quotes_history(df):
    assert isinstance(df, pd.Series)
    assert df.name == CPI
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('1991-01-31')
    assert df.shape[0] >= 326
    assert df.loc['2018-02-28'] == 1.0021


def test_update_cpi_need_update(monkeypatch):
    time.sleep(1)
    monkeypatch.setattr(local_cpi, 'UPDATE_PERIOD_IN_DAYS', 1 / (60 * 60 * 24))
    file_time = path.getmtime(cpi_path())
    update_cpi()
    assert path.getmtime(cpi_path()) > file_time


def test_validate():
    df = load_cpi()
    df.iloc[0] = 1
    with pytest.raises(ValueError) as info:
        validate(df, load_cpi())
    assert 'Новые данные CPI не совпадают с локальной версией.' in str(info.value)
