from pathlib import Path

import pandas as pd
import pytest

import local.local_dividends as local_dividends
import settings
from local.local_dividends import DividendsDataManager


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('test_local_dividends')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_monthly_dividends():
    DividendsDataManager('CHMF').update()
    DividendsDataManager('GMKN').update()
    df = local_dividends.monthly_dividends(('CHMF', 'GMKN'), pd.Timestamp('2018-07-17'))
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (102, 2)
    assert df.loc['2018-07-17', 'CHMF'] == pytest.approx(38.32 + 27.72)
    assert df.loc['2018-06-17', 'CHMF'] == pytest.approx(0)
    assert df.loc['2017-12-17', 'CHMF'] == pytest.approx(35.61)
    assert df.loc['2010-02-17', 'CHMF'] == pytest.approx(0)
    assert df.loc['2010-11-17', 'CHMF'] == pytest.approx(4.29)
    assert df.loc['2011-06-17', 'CHMF'] == pytest.approx(2.42 + 3.9)

    assert df.loc['2018-07-17', 'GMKN'] == pytest.approx(607.98)
    assert df.loc['2018-06-17', 'GMKN'] == pytest.approx(0)
    assert df.loc['2017-11-17', 'GMKN'] == pytest.approx(224.2)
    assert df.loc['2010-02-17', 'GMKN'] == pytest.approx(0)
    assert df.loc['2010-06-17', 'GMKN'] == pytest.approx(210)
    assert df.loc['2011-05-17', 'GMKN'] == pytest.approx(180)


def test_no_data_in_data_base():
    df = DividendsDataManager('TEST').value
    assert isinstance(df, pd.Series)
    assert df.name == 'TEST'
    assert len(df) == 0
    assert isinstance(df.index, pd.DatetimeIndex)
