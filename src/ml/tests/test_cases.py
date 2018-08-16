import collections
import numpy as np
import pandas as pd

from dividends_metrics import DividendsMetrics
from ml.cases import CasesIterator, all_case
from portfolio import Portfolio


def test_iterable():
    iterable = CasesIterator(tuple(['GMKN', 'LSRG', 'MSTT']), pd.Timestamp('2018-05-21'))
    assert isinstance(iterable, collections.Iterable)
    assert isinstance(iter(iterable), collections.Iterator)


def test_yields_vs_dividends_metrics():
    positions = dict(MSRS=128,
                     PRTK=0,
                     MVID=0)
    port = Portfolio(date='2017-07-31',
                     cash=7_764,
                     positions=positions)
    metrics_yields = DividendsMetrics(port).yields
    tickers = tuple(key for key in sorted(positions))
    df = CasesIterator(tickers, pd.Timestamp('2018-07-31'))._real_dividends_yields(pd.Timestamp('2018-07-31'))
    assert np.allclose(metrics_yields.iloc[:, :-2], df.iloc[:-1, :])


def test_cases_vs_dividends_metrics():
    positions = dict(MSTT=128,
                     MVID=0,
                     ALRS=0)
    port = Portfolio(date='2017-06-28',
                     cash=7_764,
                     positions=positions)
    metrics_yields = DividendsMetrics(port).yields
    tickers = tuple(key for key in sorted(positions))
    df = CasesIterator(tickers, pd.Timestamp('2018-07-31')).cases(pd.Timestamp('2018-06-28'))
    assert len(df) == 3
    assert df.index[0] == ('ALRS', pd.Timestamp('2017-06-28'))
    assert df.index[1] == ('MSTT', pd.Timestamp('2017-06-28'))
    assert df.index[2] == ('MVID', pd.Timestamp('2017-06-28'))
    assert np.allclose(metrics_yields.iloc[:, :-2].T, df.iloc[:, :-1])


def test_all_case():
    df = all_case(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-01-05'))
    assert len(df) == 6
    assert df.index[0] == ('AKRN', pd.Timestamp('2015-01-04'))
    assert df.index[2] == ('PMSBP', pd.Timestamp('2015-01-04'))
    assert df.index[4] == ('MTSS', pd.Timestamp('2015-01-05'))
    positions = dict(AKRN=128,
                     PMSBP=0,
                     MTSS=0)
    port = Portfolio(date='2015-01-05',
                     cash=7_764,
                     positions=positions)
    metrics_yields = DividendsMetrics(port).yields
    assert np.allclose(metrics_yields.iloc[:, :-2].T, df.iloc[3:, :-1])
