from pathlib import Path

import pandas as pd

from portfolio_optimizer import settings
from portfolio_optimizer.local.local_quotes import prices, volumes
from portfolio_optimizer.local.local_quotes import quotes
from portfolio_optimizer.settings import VOLUME, CLOSE_PRICE


def test_get_quotes_history(tmpdir, monkeypatch):
    data_dir = Path(tmpdir.mkdir("quotes"))
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

