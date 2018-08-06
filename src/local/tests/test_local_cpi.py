import pandas as pd
import pytest

import web
from local import local_cpi
from local.local_cpi import CPIDataManager, cpi_to_date
from web.labels import CPI


def test_cpi():
    df = local_cpi.cpi()
    assert isinstance(df, pd.Series)
    assert df.name == CPI
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('1991-01-31')
    assert df.shape[0] >= 326
    assert df.loc['2018-02-28'] == 1.0021


def test_download_all():
    manager = CPIDataManager()
    df = manager.download_all()
    assert df.equals(web.cpi())


def test_download_update():
    manager = CPIDataManager()
    with pytest.raises(NotImplementedError):
        manager.download_update()


def test_cpi_to_date(monkeypatch):
    fake_df = local_cpi.cpi()[:'2018-06-30']
    monkeypatch.setattr(local_cpi, 'cpi', lambda: fake_df)
    df = cpi_to_date(pd.Timestamp('2018-08-06'))
    assert len(df) == 332
    assert df.index[0] == pd.Timestamp('1991-01-06')
    assert df.index[-1] == pd.Timestamp('2018-08-06')
    assert df.iat[-3] == pytest.approx(1.0049)
    assert df.iat[-2] == pytest.approx(1.0007)
    assert df.iat[-1] == pytest.approx(0.9946)
