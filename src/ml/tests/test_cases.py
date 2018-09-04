import catboost
import collections
import numpy as np
import pandas as pd

from metrics.dividends_metrics_base import BaseDividendsMetrics
from metrics.portfolio import Portfolio
from ml.cases import RawCasesIterator, learn_pool, Freq, predict_pool


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
    itr = RawCasesIterator(tickers, pd.Timestamp('2018-07-31'), Freq.yearly)
    df = itr._real_dividends_yields(pd.Timestamp('2018-07-31'))
    assert np.allclose(metrics_yields, df.iloc[:, 1:-1].T)


def test_yields_vs_dividends_metrics_predicted_false():
    positions = dict(GMKN=128,
                     MSRS=0,
                     SNGSP=0)
    port = Portfolio(date='2018-08-30',
                     cash=7_764,
                     positions=positions)
    metrics_yields = BaseDividendsMetrics(port).yields
    tickers = tuple(key for key in sorted(positions))
    itr = RawCasesIterator(tickers, pd.Timestamp('2018-08-30'), Freq.yearly)
    df = itr._real_dividends_yields(pd.Timestamp('2018-08-30'), predicted=False)
    assert np.allclose(metrics_yields, df.iloc[:, 1:].T)


def test_cases_vs_dividends_metrics():
    positions = dict(MSTT=128,
                     MVID=0,
                     ALRS=0)
    port = Portfolio(date='2017-06-28',
                     cash=7_764,
                     positions=positions)
    metrics_yields = BaseDividendsMetrics(port).yields
    tickers = tuple(key for key in sorted(positions))
    df = RawCasesIterator(tickers, pd.Timestamp('2018-07-31'), Freq.yearly).cases(pd.Timestamp('2018-06-28'))
    assert len(df) == 3
    assert df.iat[0, 0] == 'ALRS'
    assert df.iat[1, 0] == 'MSTT'
    assert df.iat[2, 0] == 'MVID'
    assert np.allclose(metrics_yields.T, df.iloc[:, 1:-1])
    assert not df['y'].isnull().any()


def test_cases_vs_dividends_metrics_predicted_false():
    positions = dict(PRTK=128,
                     AKRN=0,
                     LKOH=0)
    port = Portfolio(date='2018-07-31',
                     cash=7_764,
                     positions=positions)
    metrics_yields = BaseDividendsMetrics(port).yields
    tickers = tuple(key for key in sorted(positions))
    df = RawCasesIterator(tickers, pd.Timestamp('2018-07-31'), Freq.yearly).cases(pd.Timestamp('2018-07-31'), False)
    assert len(df) == 3
    assert df.iat[0, 0] == 'AKRN'
    assert df.iat[1, 0] == 'LKOH'
    assert df.iat[2, 0] == 'PRTK'
    assert np.allclose(metrics_yields.T, df.iloc[:, 1:-1])
    assert df['y'].isnull().all()


def test_iter():
    iterator = RawCasesIterator(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-01-05'), Freq.yearly)
    df = next(iter(iterator))
    assert len(df) == 3
    assert df.iat[0, 0] == 'AKRN'
    assert df.iat[1, 0] == 'MTSS'
    assert df.iat[2, 0] == 'PMSBP'
    positions = dict(AKRN=128,
                     PMSBP=0,
                     MTSS=0)
    port = Portfolio(date='2015-01-05',
                     cash=7_764,
                     positions=positions)
    metrics_yields = BaseDividendsMetrics(port).yields
    assert np.allclose(metrics_yields.T, df.iloc[:, 1:-1])


def test_monthly_quarterly_yearly():
    monthly_data = []
    quarterly_data = []
    yearly_data = []

    monthly_data.append(learn_pool(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.monthly))
    quarterly_data.append(learn_pool(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.quarterly))
    yearly_data.append(learn_pool(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.yearly))

    monthly_data.append(predict_pool(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.monthly))
    quarterly_data.append(predict_pool(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.quarterly))
    yearly_data.append(predict_pool(tuple(['AKRN', 'MTSS', 'PMSBP']), pd.Timestamp('2016-05-18'), Freq.yearly))

    for i in range(2):
        assert isinstance(monthly_data[i], catboost.Pool)
        assert isinstance(quarterly_data[i], catboost.Pool)
        assert isinstance(yearly_data[i], catboost.Pool)

    for i in range(2):
        assert monthly_data[i].get_cat_feature_indices() == [0]
        assert quarterly_data[i].get_cat_feature_indices() == [0]
        assert yearly_data[i].get_cat_feature_indices() == [0]

    assert isinstance(monthly_data[0].get_label(), list)
    assert isinstance(quarterly_data[0].get_label(), list)
    assert isinstance(yearly_data[0].get_label(), list)

    assert monthly_data[1].get_label() is None
    assert quarterly_data[1].get_label() is None
    assert yearly_data[1].get_label() is None

    assert monthly_data[0].shape == (15, 61)
    assert quarterly_data[0].shape == (6, 21)
    assert yearly_data[0].shape == (3, 6)

    assert monthly_data[1].shape == (3, 61)
    assert quarterly_data[1].shape == (3, 21)
    assert yearly_data[1].shape == (3, 6)

    for i in range(3):
        assert monthly_data[0].get_label()[-1 - i] == quarterly_data[0].get_label()[-1 - i]
        assert quarterly_data[0].get_label()[-1 - i] == yearly_data[0].get_label()[-1 - i]

    for i in range(2):
        for year in range(5):
            m_slice = slice(1 + year * 12, 1 + (year + 1) * 12)
            y_slice = slice(1 + year, 2 + year)
            assert np.allclose(np.array(monthly_data[i].get_features())[-3:, m_slice].sum(axis=1, keepdims=True),
                               np.array(yearly_data[i].get_features())[-3:, y_slice])
            q_slice = slice(1 + year * 4, 1 + (year + 1) * 4)
            assert np.allclose(np.array(quarterly_data[i].get_features())[-3:, q_slice].sum(axis=1, keepdims=True),
                               np.array(yearly_data[i].get_features())[-3:, y_slice])
