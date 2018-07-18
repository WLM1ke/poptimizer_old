from pathlib import Path

import pandas as pd
import pytest
from portfolio_optimizer.local.data_file import DataFile

import settings


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('local_storage')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_no_index():
    data = DataFile('folder1', 'df1')
    assert data.last_update() is None


def test_dump():
    data = DataFile('folder1', 'df1')
    df = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
    data.dump(df)
    assert data.last_update() is not None
    assert data.load().equals(df)


def test_no_file():
    data = DataFile('folder1', 'df2')
    assert data.last_update() is None


def test_second_dump():
    data = DataFile('folder1', 'df1')
    df1 = data.load()
    time1 = data.last_update()
    df2 = pd.DataFrame(data={'col1': [1, 1], 'col2': [1, 1]})
    data.dump(df2)
    assert data.last_update() > time1
    assert not data.load().equals(df1)
    assert data.load().equals(df2)
