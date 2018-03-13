from pathlib import Path

import arrow
import pandas as pd
import pytest

from portfolio import download, settings
from portfolio.getter import history
from portfolio.getter.history import get_quotes_history, load_quotes_history, df_last_date, validate_last_date


@pytest.fixture(scope='class')
def new_df(tmpdir_factory):
    # Этап 1 - инициируется создание DataFrame с нуля во временной директории
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('data')
    settings.DATA_PATH = Path(temp_dir)
    yield get_quotes_history('MSTT')
    settings.DATA_PATH = saved_path


@pytest.fixture(scope='class')
def updated_df():
    # Этап 2 - иницируется обновление DataFrame путем подмены параметра окончания торгового дня
    saved_date = history.END_OF_CURRENT_TRADING_DAY
    history.END_OF_CURRENT_TRADING_DAY = arrow.get().shift(months=1)
    df2 = get_quotes_history('MSTT')
    history.END_OF_CURRENT_TRADING_DAY = saved_date
    return df2


@pytest.fixture(scope='class')
def no_update_df():
    # Этап 3 - повторный вызов без обновления с вовращенным параметром окончания торгового дня
    return get_quotes_history('MSTT')


@pytest.fixture(scope='class', params=range(3))
def df(request, new_df, updated_df, no_update_df):
    dfs = [new_df, updated_df, no_update_df]
    return dfs[request.param]


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
