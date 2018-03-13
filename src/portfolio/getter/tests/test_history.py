from pathlib import Path

import arrow
import pandas as pd
import pytest

from portfolio import download, settings
from portfolio.getter import history
from portfolio.getter.history import get_quotes_history, load_quotes_history, df_last_date, validate_last_date


def updated_df():
    saved_date = history.END_OF_CURRENT_TRADING_DAY
    history.END_OF_CURRENT_TRADING_DAY = arrow.get().shift(months=1)
    df2 = get_quotes_history('MSTT')
    history.END_OF_CURRENT_TRADING_DAY = saved_date
    return df2


@pytest.fixture(scope='class')
def make_dfs(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('data')
    settings.DATA_PATH = Path(temp_dir)
    dfs = [get_quotes_history('MSTT'), updated_df(), get_quotes_history('MSTT')]
    settings.DATA_PATH = saved_path
    return dfs


@pytest.fixture(scope='class', params=range(3))
def df(request, make_dfs):
    return make_dfs[request.param]


class TestGetQuotesHistory:
    def test_df_type(self, df):
        assert isinstance(df, pd.DataFrame)

    def test_df_columns_number(self, df):
        assert len(df.columns) == 2

    def test_df_index_monotonic(self, df):
        assert df.index.is_monotonic_increasing

    def test_df_is_unique(self, df):
        assert df.index.is_unique

    def test_beginning_date(self, df):
        assert df.index[0] == pd.to_datetime('2010-11-03')

    def test_load_long_data(self, df):
        assert df.shape[0] > 100

    def test_checkpoint(self, df):
        assert df.loc['2018-03-09', 'CLOSE'] == 148.8 and df.loc['2018-03-09', 'VOLUME'] == 2960


def test_validate_last_date_error():
    df_old = load_quotes_history('AKRN')
    df_new = download.quotes_history('MSTT', df_last_date(df_old))
    with pytest.raises(ValueError) as info:
        validate_last_date(df_old, df_new)
    assert 'Загруженные данные не стыкуются с локальными.' in str(info.value)
