import collections
import numpy as np
import pandas as pd
import pytest

from dividends_metrics import DividendsMetrics
from ml.cases import CasesIterator, all_case, CasesDataManager
from portfolio import Portfolio
from utils.data_file import DataFile


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


def test_iter():
    iterator = CasesIterator(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-01-05'))
    df = next(iter(iterator))
    assert len(df) == 3
    assert df.index[0] == ('AKRN', pd.Timestamp('2015-01-04'))
    assert df.index[1] == ('MTSS', pd.Timestamp('2015-01-04'))
    assert df.index[2] == ('PMSBP', pd.Timestamp('2015-01-04'))
    positions = dict(AKRN=128,
                     PMSBP=0,
                     MTSS=0)
    port = Portfolio(date='2015-01-04',
                     cash=7_764,
                     positions=positions)
    metrics_yields = DividendsMetrics(port).yields
    assert np.allclose(metrics_yields.iloc[:, :-2].T, df.iloc[:, :-1])


@pytest.fixture(name='params')
def get_params():
    df = DataFile(None, 'cases').value
    tickers = tuple(set(df.index.levels[0]))
    date = df.index[-1][1] + pd.DateOffset(years=1)
    lags = df.shape[1] - 1
    return tickers, date, lags


def test_errors(params):
    tickers, date, lags = params
    with pytest.raises(ValueError) as info:
        all_case(tickers, date, lags + 1)
    assert 'лагов' in str(info.value)
    with pytest.raises(ValueError) as info:
        all_case(tickers, date + pd.DateOffset(months=-1), lags)
    assert 'даты' in str(info.value)
    with pytest.raises(ValueError) as info:
        all_case(tickers[:-1], date, lags)
    assert 'тикеров' in str(info.value)


def test_download_all(params):
    manager = CasesDataManager(*params)
    manager._params = (tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-01-05'), 5)
    df = manager.download_all()
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


def test_download_update(params):
    manager = CasesDataManager(*params)
    with pytest.raises(NotImplementedError):
        CasesDataManager(*params).download_update()
