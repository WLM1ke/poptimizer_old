from pathlib import Path

import pytest

import settings
import web
from local import local_dividends_smart_lab


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('test_local_dividends_smart_lab')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_dividends_smart_lab_first_time():
    df = local_dividends_smart_lab.dividends_smart_lab()
    assert df.equals(web.dividends_smart_lab())


def test_need_not_update():
    manager = local_dividends_smart_lab.SmartLabDataManager()
    assert not manager._need_update()


def test_need_update_true(monkeypatch):
    monkeypatch.setattr(local_dividends_smart_lab.SmartLabDataManager, 'days_to_update', 0)
    manager = local_dividends_smart_lab.SmartLabDataManager()
    assert manager._need_update()
