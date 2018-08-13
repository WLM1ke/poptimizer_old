import pandas as pd
import pytest

import local
from dividends_metrics import DividendsMetrics
from local.local_dividends import STATISTICS_START
from ml.cases_non_overlapping import cases_non_overlapping
from ml.cases_non_overlapping import real_after_tax_yearly_dividends, real_yearly_price, real_prices_and_dividends
from portfolio import Portfolio
from web.labels import TICKER, DATE

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


def test_real_prices_and_dividends():
    data = real_prices_and_dividends(TICKERS, LAST_DATE)
    assert isinstance(data, tuple)
    assert isinstance(data[0], pd.DataFrame)
    assert isinstance(data[1], pd.DataFrame)
    assert data[0].shape == (7, 3)
    assert data[1].shape == (7, 3)


def test_cases_non_overlapping():
    df = cases_non_overlapping(TICKERS, LAST_DATE)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (6, 8)
    assert df.loc[4, TICKER] == 'MSTT'
    assert df.loc[4, DATE] == pd.Timestamp('2015-05-21')
    assert df.loc[4, 'lag - 0'] == pytest.approx(0.0652182463488862)
    assert df.loc[4, 'lag - 1'] == pytest.approx(0.0748216152993375)
    assert df.loc[4, 'lag - 2'] == pytest.approx(0.0)
    assert df.loc[0, TICKER] == 'GMKN'
    assert df.loc[1, DATE] == pd.Timestamp('2016-05-21')
    assert df.loc[0, 'lag - 3'] == pytest.approx(0.06468912781277)
    assert df.loc[2, TICKER] == 'LSRG'
    assert df.loc[2, DATE] == pd.Timestamp('2015-05-21')
    assert df.loc[3, 'lag - 4'] == pytest.approx(0.0365196778541529)
    assert df.loc[4, 'lag - 5'] == pytest.approx(0.0834746226712652)


def test_vs_dividends_metrics():
    positions = dict(AKRN=563,
                     PMSBP=2796,
                     UPRO=986)
    port = Portfolio(date='2017-07-31',
                     cash=7_764,
                     positions=positions)
    metrics_yields = DividendsMetrics(port).yields
    tickers = tuple(key for key in positions)
    cases = cases_non_overlapping(tickers, pd.Timestamp('2018-07-31'))
    assert metrics_yields.loc['2017-07-31', 'AKRN'] == pytest.approx(cases.loc[2, 'lag - 1'])
    assert metrics_yields.loc['2013-07-31', 'PMSBP'] == pytest.approx(cases.loc[5, 'lag - 5'])
    assert metrics_yields.loc['2014-07-31', 'UPRO'] == pytest.approx(cases.loc[8, 'lag - 4'])
    assert metrics_yields.loc['2015-07-31', 'AKRN'] == pytest.approx(cases.loc[2, 'lag - 3'])
    assert metrics_yields.loc['2016-07-31', 'PMSBP'] == pytest.approx(cases.loc[5, 'lag - 2'])
    assert metrics_yields.loc['2017-07-31', 'UPRO'] == pytest.approx(cases.loc[8, 'lag - 1'])
