import pandas as pd
import pytest

from portfolio import download
from portfolio.getter.history import get_quotes_history, load_quotes_history, df_last_date, validate_last_date


@pytest.fixture(scope='class')
def get_df():
    return get_quotes_history('MSTT')


class TestGetQuotesHistory:
    def test_df_type(self, get_df):
        assert isinstance(get_df, pd.DataFrame)

    def test_df_columns_number(self, get_df):
        assert len(get_df.columns) == 2

    def test_df_index_monotonic(self, get_df):
        assert get_df.index.is_monotonic_increasing

    def test_df_is_unique(self, get_df):
        assert get_df.index.is_unique

    def test_beginning_date(self, get_df):
        assert get_df.index[0] == pd.to_datetime('2010-11-03')

    def test_load_long_data(self, get_df):
        assert get_df.shape[0] > 100

    def test_checkpoint(self, get_df):
        assert get_df.loc['2018-03-09', 'CLOSE'] == 148.8 and get_df.loc['2018-03-09', 'VOLUME'] == 2960


@pytest.fixture(scope='class')
def df_old():
    ticker = 'AKRN'
    return load_quotes_history(ticker)


class TestValidateLastDate:
    def test_validate_last_date(self, df_old):
        df_new = download.quotes_history('AKRN', df_last_date(df_old))
        assert validate_last_date(df_old, df_new) is None

    def test_validate_last_date_error(self, df_old):
        df_new = download.quotes_history('MSTT', df_last_date(df_old))
        with pytest.raises(ValueError) as info:
            validate_last_date(df_old, df_new)
        assert 'Загруженные данные не стыкуются с локальными.' == str(info.value)
