import pathlib

import pandas as pd
import pytest

import settings
from local.dividends import comony_ru


def test_dividends(monkeypatch, tmpdir):
    data_path = pathlib.Path(tmpdir.mkdir("conomy"))
    monkeypatch.setattr(settings, 'DATA_PATH', data_path)
    df = comony_ru.dividends_conomy('CHMF')
    assert isinstance(df, pd.Series)
    assert df.name == 'CHMF'
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.Timestamp('2006-08-06')
    assert df['2018-06-19'] == pytest.approx(66.04)


def test_download_update():
    with pytest.raises(NotImplementedError) as error:
        comony_ru.ConomyDataManager('AKRN').download_update()
    assert error.type == NotImplementedError
