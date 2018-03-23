from pathlib import Path

import arrow
import pandas as pd
import pytest

from optimizer import download, settings
from optimizer.getter import local_quotes
from optimizer.getter.local_index import LocalIndex, get_index_history
from optimizer.getter.local_quotes import get_prices_history, get_volumes_history
from optimizer.getter.local_quotes import get_quotes_history, LocalQuotes
from optimizer.settings import VOLUME, CLOSE_PRICE


def updated_df():
    saved_date = local_quotes.END_OF_CURRENT_TRADING_DAY
    local_quotes.END_OF_CURRENT_TRADING_DAY = arrow.get().shift(months=1)
    df2 = get_quotes_history('MSTT')
    local_quotes.END_OF_CURRENT_TRADING_DAY = saved_date
    return df2


@pytest.fixture(scope='module', name='dfs', autouse=True)
def make_dfs_and_fake_path(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('data')
    settings.DATA_PATH = Path(temp_dir)
    dfs = [get_quotes_history('MSTT'), updated_df(), get_quotes_history('MSTT')]
    yield dfs
    settings.DATA_PATH = saved_path


@pytest.fixture(params=range(3), name='df')
def yield_df(request, dfs):
    return dfs[request.param]


def test_get_quotes_history(df):
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 2
    assert df.index.is_monotonic_increasing
    assert df.index.is_unique
    assert df.index[0] == pd.to_datetime('2010-11-03')
    assert df.shape[0] > 100
    assert df.loc['2018-03-09', CLOSE_PRICE] == 148.8 and df.loc['2018-03-09', VOLUME] == 2960


@pytest.fixture(scope='module', name='index_cases')
def make_index_cases():
    df1 = get_index_history()
    index = LocalIndex()
    index.update_local_history()
    df2 = index.df
    save_need_update = index.need_update
    index.need_update = lambda: True
    index.update_local_history()
    df3 = index.df
    index.need_update = save_need_update
    return df1, df2, df3


@pytest.fixture(params=range(3), name='index_df')
def yield_index_df(request, index_cases):
    return index_cases[request.param]


def test_get_index_history(index_df):
    assert isinstance(index_df, pd.Series)
    assert index_df.index.is_monotonic_increasing
    assert index_df.index.is_unique
    assert index_df.index[0] == pd.to_datetime('2003-02-26')
    assert index_df.shape[0] > 100
    assert index_df.loc['2018-03-16'] == 3281.58


def test_validate_last_date_error():
    df_old = LocalQuotes('MSTT')
    df_new = download.quotes_history('AKRN', df_old.df_last_date)
    with pytest.raises(ValueError) as info:
        df_old._validate_new_data(df_new)
    assert 'Загруженные данные MSTT не стыкуются с локальными.' in str(info.value)


def test_get_volumes_history():
    df = get_volumes_history(['KBTK', 'RTKMP'])
    assert df.loc['2018-03-09', 'KBTK'] == 0
    assert df.loc['2018-03-13', 'RTKMP'] == 400100


def test_get_prices_history():
    df = get_prices_history(['KBTK', 'RTKMP'])
    assert pd.isna(df.loc['2018-03-09', 'KBTK'])
    assert df.loc['2018-03-13', 'RTKMP'] == 62


def test_end_of_last_trading_day(monkeypatch):
    monkeypatch.setattr(local_quotes, "END_OF_CURRENT_TRADING_DAY",
                        arrow.get().to(local_quotes.MARKET_TIME_ZONE).replace(minute=0, second=0, microsecond=0))
    assert local_quotes.end_of_last_trading_day() == local_quotes.END_OF_CURRENT_TRADING_DAY
