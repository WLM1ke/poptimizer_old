import collections
import numpy as np
import pandas as pd

from dividends_metrics_base import BaseDividendsMetrics
from ml.cases import RawCasesIterator, all_cases, Freq, Cases
from portfolio import Portfolio


def test_iterable():
    iterable = RawCasesIterator(tuple(['GMKN', 'LSRG', 'MSTT']), pd.Timestamp('2018-05-21'), Freq.quarterly)
    assert isinstance(iterable, collections.Iterable)
    assert isinstance(iter(iterable), collections.Iterator)


def test_yields_vs_dividends_metrics():
    positions = dict(MSRS=128,
                     PRTK=0,
                     MVID=0)
    port = Portfolio(date='2017-07-31',
                     cash=7_764,
                     positions=positions)
    metrics_yields = BaseDividendsMetrics(port).yields
    tickers = tuple(key for key in sorted(positions))
    df = RawCasesIterator(tickers, pd.Timestamp('2018-07-31'), Freq.yearly)._real_dividends_yields(
        pd.Timestamp('2018-07-31'))
    assert np.allclose(metrics_yields, df.iloc[:, :-1].T)


def test_cases_vs_dividends_metrics():
    positions = dict(MSTT=128,
                     MVID=0,
                     ALRS=0)
    port = Portfolio(date='2017-06-28',
                     cash=7_764,
                     positions=positions)
    metrics_yields = BaseDividendsMetrics(port).yields
    tickers = tuple(key for key in sorted(positions))
    df = RawCasesIterator(tickers, pd.Timestamp('2018-07-31'), Freq.yearly).raw_cases(pd.Timestamp('2018-06-28'))
    assert len(df) == 3
    assert df.index[0] == ('ALRS', pd.Timestamp('2017-06-28'))
    assert df.index[1] == ('MSTT', pd.Timestamp('2017-06-28'))
    assert df.index[2] == ('MVID', pd.Timestamp('2017-06-28'))
    assert np.allclose(metrics_yields.T, df.iloc[:, :-1])


def test_iter():
    iterator = RawCasesIterator(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-01-05'), Freq.yearly)
    df = next(iter(iterator))
    assert len(df) == 3
    assert df.index[0] == ('AKRN', pd.Timestamp('2015-01-05'))
    assert df.index[1] == ('MTSS', pd.Timestamp('2015-01-05'))
    assert df.index[2] == ('PMSBP', pd.Timestamp('2015-01-05'))
    positions = dict(AKRN=128,
                     PMSBP=0,
                     MTSS=0)
    port = Portfolio(date='2015-01-05',
                     cash=7_764,
                     positions=positions)
    metrics_yields = BaseDividendsMetrics(port).yields
    assert np.allclose(metrics_yields.T, df.iloc[:, :-1])


def test_monthly_quarterly_yearly():
    monthly_data = all_cases(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.monthly)
    quarterly_data = all_cases(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.quarterly)
    yearly_data = all_cases(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.yearly)

    assert isinstance(monthly_data, Cases)
    assert isinstance(quarterly_data, Cases)
    assert isinstance(yearly_data, Cases)

    assert monthly_data.groups is None
    assert quarterly_data.groups is None
    assert yearly_data.groups is None

    assert isinstance(monthly_data.y, pd.Series)
    assert isinstance(quarterly_data.y, pd.Series)
    assert isinstance(yearly_data.y, pd.Series)

    assert isinstance(monthly_data.x, pd.DataFrame)
    assert isinstance(quarterly_data.x, pd.DataFrame)
    assert isinstance(yearly_data.x, pd.DataFrame)

    assert len(monthly_data.y) == 15
    assert len(quarterly_data.y) == 6
    assert len(yearly_data.y) == 3

    assert monthly_data.y.index[0] == ('AKRN', pd.Timestamp('2015-01-18'))
    assert quarterly_data.y.index[0] == ('AKRN', pd.Timestamp('2015-02-18'))
    assert yearly_data.y.index[0] == ('AKRN', pd.Timestamp('2015-05-18'))

    assert monthly_data.y.index[-1] == ('PMSBP', pd.Timestamp('2015-05-18'))
    assert quarterly_data.y.index[-1] == ('PMSBP', pd.Timestamp('2015-05-18'))
    assert yearly_data.y.index[-1] == ('PMSBP', pd.Timestamp('2015-05-18'))

    assert monthly_data.y.iloc[-3:].equals(quarterly_data.y.iloc[-3:])
    assert quarterly_data.y.iloc[-3:].equals(yearly_data.y.iloc[-3:])

    assert monthly_data.x.iloc[-3:, :3].equals(quarterly_data.x.iloc[-3:, :3])
    assert quarterly_data.x.iloc[-3:, :3].equals(yearly_data.x.iloc[-3:, :3])

    assert np.allclose(monthly_data.x.iloc[-3:, 3:15].sum(axis='columns'), yearly_data.x.iloc[-3:, 3])
    assert np.allclose(quarterly_data.x.iloc[-3:, 7:11].sum(axis='columns'), yearly_data.x.iloc[-3:, 4])
