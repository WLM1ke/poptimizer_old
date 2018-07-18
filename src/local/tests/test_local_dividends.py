from pathlib import Path

import pandas as pd
import portfolio_optimizer.local.local_dividends as local_dividends
import pytest
from portfolio_optimizer.local.local_dividends import DividendsDataManager

import settings


@pytest.fixture(scope='module', autouse=True)
def make_temp_dir(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('test_local_dividends')
    settings.DATA_PATH = Path(temp_dir)
    yield
    settings.DATA_PATH = saved_path


def test_need_update_no_data():
    manager = DividendsDataManager('AKRN')
    assert manager.need_update() == 'Нет локальных данных'


def test_need_update_ok():
    manager = DividendsDataManager('AKRN')
    manager.update()
    assert manager.need_update() == 'OK'


def test_need_update_wrong_data():
    manager = DividendsDataManager('AKRN')
    df = manager.get()
    df.loc['2018-01-23'] = -1000
    manager._file.dump(df)
    assert manager.need_update() == 'В источнике portfolio_optimizer.local.local_dividends_dohod не совпадают данные'


def test_need_update_less_data():
    manager = DividendsDataManager('AKRN')
    df = manager.get()
    df = df.drop(pd.Timestamp('2018-01-23'))
    manager._file.dump(df)
    msg = 'В источнике portfolio_optimizer.local.local_dividends_dohod присутствуют дополнительные данные'
    assert msg in manager.need_update()


def test_need_update_long_ago(monkeypatch):
    monkeypatch.setattr(local_dividends, 'DAYS_TO_MANUAL_UPDATE', 0)
    manager = DividendsDataManager('AKRN')
    assert manager.need_update() == 'Последнее обновление более 0 дней назад'


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


def test_dividends_update_status():
    DividendsDataManager('MSTT').update()
    result = local_dividends.dividends_update_status(('CHMF', 'GMKN', 'AKRN', 'BANEP', 'MSTT'))
    assert isinstance(result, pd.Series)
    assert len(result) == 5
    assert result.iloc[0] == 'OK'
    assert result.iloc[1] == 'OK'
    msg = 'В источнике portfolio_optimizer.local.local_dividends_dohod присутствуют дополнительные данные'
    assert msg in result.iloc[2]
    assert result.iloc[3] == 'Нет локальных данных'
    assert result.iloc[4] == 'В источнике portfolio_optimizer.local.local_dividends_dohod не совпадают данные'
