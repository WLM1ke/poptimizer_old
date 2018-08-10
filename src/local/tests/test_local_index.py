import arrow
import pandas as pd

from local import local_index
from local.local_index import IndexDataManager
from web.labels import CLOSE_PRICE


def test_index():
    df = local_index.index()
    assert isinstance(df, pd.Series)
    assert df.name == CLOSE_PRICE
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('2003-02-26')
    assert df.shape[0] > 100
    assert df.loc['2018-03-16'] == 3281.58


def test_download_all():
    manager = IndexDataManager()
    df = manager.value
    assert df.equals(manager.download_all())


def test_update():
    manager = IndexDataManager()
    df = manager.value
    time0 = arrow.now()
    assert manager.last_update < time0
    manager.update()
    assert manager.last_update > time0
    assert df.equals(manager.value)
