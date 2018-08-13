import pandas as pd
import pytest

import local
from local.local_dividends import STATISTICS_START
from ml.cases_non_overlapping import real_after_tax_yearly_dividends, real_yearly_price

TICKERS = tuple(['GMKN', 'LSRG', 'MSTT'])
LAST_DATE = pd.Timestamp('2017-05-21')
START_DATE = (pd.Timestamp(STATISTICS_START)
              + pd.DateOffset(month=LAST_DATE.month, day=LAST_DATE.day)
              + pd.DateOffset(days=1))
CUM_CPI = local.cpi_to_date(LAST_DATE)[START_DATE:].cumprod()


def test_real_after_tax_yearly_dividends():
    df = real_after_tax_yearly_dividends(TICKERS, START_DATE, LAST_DATE, CUM_CPI)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (7, 3)
    assert df.index[0] == pd.Timestamp('2011-05-21')
    assert df.index[-1] == LAST_DATE
    assert df.loc['2013-05-21', 'MSTT'] == pytest.approx(5.56517757328837)
    assert df.loc['2015-05-21', 'LSRG'] == pytest.approx(71.0671356752115)
    assert df.loc['2017-05-21', 'GMKN'] == pytest.approx(352.624894944916)
    assert df.loc['2014-05-21', 'LSRG'] == pytest.approx(0.0)
    assert df.loc['2011-05-21', 'GMKN'] == pytest.approx(142.894781856063)


def test_real_yearly_price():
    index = real_after_tax_yearly_dividends(TICKERS, START_DATE, LAST_DATE, CUM_CPI).index
    cum_cpi = CUM_CPI.reindex(index)
    df = real_yearly_price(TICKERS, START_DATE, cum_cpi)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (7, 3)
    assert df.index[0] == pd.Timestamp('2011-05-21')
    assert df.index[-1] == LAST_DATE
    assert df.loc['2013-05-21', 'MSTT'] == pytest.approx(123.178554598867)
    assert df.loc['2015-05-21', 'LSRG'] == pytest.approx(403.573254938555)
    assert df.loc['2017-05-21', 'GMKN'] == pytest.approx(4895.27063342009)
    assert df.loc['2014-05-21', 'LSRG'] == pytest.approx(419.242534710405)
    assert df.loc['2011-05-21', 'GMKN'] == pytest.approx(6396.50332574073)
