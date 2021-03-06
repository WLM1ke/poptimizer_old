from pathlib import Path

import arrow
import numpy as np
import pandas as pd

import settings
from local.moex.iss_quotes import prices, volumes, QuotesDataManager
from local.moex.iss_quotes import quotes
from web.labels import CLOSE_PRICE, VOLUME


def test_get_quotes_history(tmpdir, monkeypatch):
    data_dir = Path(tmpdir.mkdir("test_quotes"))
    monkeypatch.setattr(settings, 'DATA_PATH', data_dir)
    df = quotes('MSTT')
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 2
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('2010-11-03')
    assert df.shape[0] > 100
    assert df.loc['2018-03-09', CLOSE_PRICE] == 148.8
    assert df.loc['2018-03-09', VOLUME] == 2960


def test_volumes():
    df = volumes(('KBTK', 'RTKMP'))
    assert df.loc['2018-03-09', 'KBTK'] == 0
    assert df.loc['2018-03-13', 'RTKMP'] == 400100


def test_prices():
    df = prices(('KBTK', 'RTKMP'))
    assert pd.isna(df.loc['2018-03-09', 'KBTK'])
    assert df.loc['2018-03-13', 'RTKMP'] == 62


def test_update():
    manager = QuotesDataManager('RTKMP')
    data = manager.value.values
    time0 = arrow.now()
    assert manager.last_update < time0
    manager.update()
    assert manager.last_update > time0
    assert np.allclose(manager.value.values, data, equal_nan=True)
