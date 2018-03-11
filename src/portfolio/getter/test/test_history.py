import pandas as pd
import pytest

from portfolio.getter.history import get_quotes_history


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
