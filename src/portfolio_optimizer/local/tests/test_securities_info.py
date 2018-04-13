from pathlib import Path

import pytest

import portfolio_optimizer.local.storage_old
from portfolio_optimizer import settings
from portfolio_optimizer.local import local_securities_info
from portfolio_optimizer.settings import LOT_SIZE, COMPANY_NAME, REG_NUMBER


@pytest.fixture(scope='class')
def security_info_fake_data_path(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('security_info')
    settings.DATA_PATH = Path(temp_dir)
    local_securities_info.DATA_PATH = portfolio_optimizer.local.storage_old.make_data_path('securities_info',
                                                                                        'securities_info.csv')
    yield
    settings.DATA_PATH = saved_path
    local_securities_info.DATA_PATH = portfolio_optimizer.local.storage_old.make_data_path('securities_info',
                                                                                        'securities_info.csv')


@pytest.mark.usefixtures('security_info_fake_data_path')
class TestSecurityInfo:
    def test_first_time_get_last_prices(self):
        df = local_securities_info.last_price(['KBTK', 'MOEX'])
        assert len(df.index) == 2
        assert len(local_securities_info.load_securities_info().index) == 2

    def test_second_time_security_info(self):
        df = local_securities_info.get_security_info(['KBTK', 'MOEX'])
        assert len(df.index) == 2
        assert len(local_securities_info.load_securities_info().index) == 2

    def test_all_tickers_in_local_data_security_info(self):
        df = local_securities_info.get_security_info(['MOEX'])
        assert len(df.index) == 1
        assert len(local_securities_info.load_securities_info().index) == 2

    def test_not_all_tickers_in_local_data_security_info(self):
        df = local_securities_info.get_security_info(['MOEX', 'MTSS'])
        assert len(df.index) == 2
        assert len(local_securities_info.load_securities_info().index) == 3

    def test_all_tickers_are_new_time_security_info(self):
        df = local_securities_info.get_security_info(['SNGSP', 'GAZP'])
        assert len(df.index) == 2
        assert len(df.columns) == 5
        df_local = local_securities_info.load_securities_info()
        assert len(df_local.index) == 5
        assert df.equals(df_local.loc[['SNGSP', 'GAZP']])
        assert df_local.loc['KBTK', COMPANY_NAME] == 'КузбТК ао'
        assert df_local.loc['MOEX', REG_NUMBER] == '1-05-08443-H'
        assert df.loc['SNGSP', LOT_SIZE] == 100


@pytest.fixture(scope='class')
def get_reg_number_tickers_fake_data_path(tmpdir_factory):
    saved_path = settings.DATA_PATH
    temp_dir = tmpdir_factory.mktemp('data_get_tickers')
    settings.DATA_PATH = Path(temp_dir)
    local_securities_info.DATA_PATH = portfolio_optimizer.local.storage_old.make_data_path('securities_info',
                                                                                        'securities_info.csv')
    yield
    settings.DATA_PATH = saved_path
    local_securities_info.DATA_PATH = portfolio_optimizer.local.storage_old.make_data_path('securities_info',
                                                                                        'securities_info.csv')


@pytest.mark.usefixtures('get_reg_number_tickers_fake_data_path')
class TestGetRegNumberTickers:
    def test_first_get_reg_number_tickers(self):
        assert local_securities_info.aliases(['UPRO']).loc['UPRO'] == 'UPRO EONR OGK4'

    def test_download_tickers_for_get_reg_number_tickers(self):
        assert local_securities_info.aliases(['TTLK']).loc['TTLK'] == 'TTLK'

    def test_load_local_tickers_for_get_reg_number_tickers(self):
        assert local_securities_info.aliases(['UPRO']).loc['UPRO'] == 'UPRO EONR OGK4'
