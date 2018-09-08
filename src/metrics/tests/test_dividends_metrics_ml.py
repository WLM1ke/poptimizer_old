import numpy as np
import pandas as pd

import metrics
from metrics.ml_dividends import model


def test_tickers_real_after_tax_mean():
    positions = dict(GMKN=146, MSTT=1823, NLMK=507, TTLK=234, PRTK=0)
    date = '2018-09-04'
    portfolio = metrics.Portfolio(date, 0, positions)
    dividends_metrics = metrics.MLDividendsMetrics(portfolio)
    dividends_model = model.DividendsML(tuple(sorted(positions)), pd.Timestamp(date))
    assert dividends_metrics._tickers_real_after_tax_mean.equals(dividends_model.div_prediction)


def test_tickers_real_after_tax_std():
    positions = dict(GMKN=146, MSTT=1823, NLMK=507, TTLK=234, PRTK=0)
    date = '2018-09-04'
    portfolio = metrics.Portfolio(date, 0, positions)
    dividends_metrics = metrics.MLDividendsMetrics(portfolio)
    dividends_model = model.DividendsML(tuple(sorted(positions)), pd.Timestamp(date))
    assert isinstance(dividends_metrics._tickers_real_after_tax_std, pd.Series)
    assert dividends_metrics._tickers_real_after_tax_std.index.equals(pd.Index(sorted(positions)))
    assert np.allclose(dividends_metrics._tickers_real_after_tax_std.values, dividends_model.std)
