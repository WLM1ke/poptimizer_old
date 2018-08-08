from pathlib import Path

import arrow
import pandas as pd
import pytest

import settings
from local_new import data_manager


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('data_manager')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


@pytest.fixture(scope='module', name='data_manager_class')
def test_data_manager():
    class DataManager(data_manager.AbstractDataManager):
        def download_all(self):
            return pd.DataFrame(data={'col1': [1, 2], 'col2': ['a', 'f']})

        def download_update(self):
            return pd.DataFrame(data={'col1': [2, 5], 'col2': ['f', 't']}, index=[1, 2])

    return DataManager


def test_data_manager_create(data_manager_class):
    t0 = arrow.now()
    data = data_manager_class('cat8', 'data5')
    assert data.value.equals(pd.DataFrame(data={'col1': [1, 2], 'col2': ['a', 'f']}))
    assert t0 < data.last_update
    assert data.last_update < data.next_update


def test_data_manager_update(monkeypatch, data_manager_class):
    time = arrow.now().shift(days=1).replace(hour=20)

    def fake_now():
        return time

    monkeypatch.setattr(arrow, 'now', fake_now)
    data = data_manager_class('cat8', 'data5')
    assert data.value.equals(pd.DataFrame(data={'col1': [1, 2, 5], 'col2': ['a', 'f', 't']}))


def test_this_day_update(monkeypatch, data_manager_class):
    data = data_manager_class('cat8', 'data5')
    fake_end_of_trading_day = dict(hour=data.last_update.hour,
                                   minute=59,
                                   second=59,
                                   microsecond=999999)
    monkeypatch.setattr(data_manager, 'END_OF_TRADING_DAY', fake_end_of_trading_day)
    assert data.next_update == data.last_update.replace(**fake_end_of_trading_day)


def test_next_day_update(monkeypatch, data_manager_class):
    data = data_manager_class('cat8', 'data5')
    fake_end_of_trading_day = dict(hour=data.last_update.hour,
                                   minute=0,
                                   second=0,
                                   microsecond=0)
    monkeypatch.setattr(data_manager, 'END_OF_TRADING_DAY', fake_end_of_trading_day)
    assert data.next_update == data.last_update.shift(days=1).replace(**fake_end_of_trading_day)


def test_from_scratch(monkeypatch, data_manager_class):
    monkeypatch.setattr(data_manager.AbstractDataManager, 'update_from_scratch', True)
    data = data_manager_class('cat8', 'data5')
    data.update()
    assert data.value.equals(pd.DataFrame(data={'col1': [1, 2], 'col2': ['a', 'f']}))


def test_no_download_update_and_series():
    class DataManager(data_manager.AbstractDataManager):
        def download_all(self):
            return pd.Series(data=[1, 2])

        def download_update(self):
            super().download_update()

    data = DataManager('cat1', 'data5')
    time0 = data.last_update
    data.update()
    assert data.value.equals(pd.Series(data=[1, 2]))
    assert data.last_update > time0


def test_non_unique():
    class DataManager(data_manager.AbstractDataManager):
        def download_all(self):
            return pd.Series(data=[1, 2], index=[1, 1])

        def download_update(self):
            super().download_update()

    with pytest.raises(ValueError) as error_info:
        DataManager('cat6', 'data1')
    assert 'У новых данных индекс не уникальный' == str(error_info.value)


def test_non_monotonic():
    class DataManager(data_manager.AbstractDataManager):
        def download_all(self):
            return pd.Series(data=[1, 2], index=[1, 2])

        def download_update(self):
            return pd.Series(data=[2, 3], index=[2, 0])

    data = DataManager('cat1', 'data0')
    with pytest.raises(ValueError) as error_info:
        data.update()
    assert 'У новых данных индекс не возрастает монотонно' == str(error_info.value)


def test_data_not_stacks():
    class DataManager(data_manager.AbstractDataManager):
        def download_all(self):
            return pd.Series(data=[1, 2], index=[2, 5])

        def download_update(self):
            return pd.Series(data=[1, 4], index=[5, 6])

    data = DataManager('cat2', 'data8')
    with pytest.raises(ValueError) as error_info:
        data.update()
    assert 'Ошибка обновления данных - существующие данные не соответствуют новым:' in str(error_info.value)


def test_str(data_manager_class):
    string = str(data_manager_class('cat8', 'data5'))
    assert 'Последнее обновление -' in string
    assert 'Следующее обновление - ' in string


def test_utcoffset(data_manager_class):
    data = data_manager_class('cat8', 'data5')
    assert data.last_update.utcoffset().seconds == 10800
    assert data.next_update.utcoffset().seconds == 10800
