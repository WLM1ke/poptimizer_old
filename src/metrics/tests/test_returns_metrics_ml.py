import numpy as np
import pandas as pd
import pytest

import metrics
from metrics import CASH, PORTFOLIO
from ml.returns import model
from ml.returns.manager import ReturnsMLDataManager

POSITIONS = dict(AKRN=563,
                 BANEP=488,
                 LKOH=318,
                 PIKK=107,
                 TTLK=198)

DATE = '2018-10-15'
TEST_CASH = 23_437


@pytest.fixture(scope='module', name='data')
def make_metrics():
    portfolio = metrics.Portfolio(DATE, TEST_CASH, POSITIONS)
    return metrics.MLReturnsMetrics(portfolio)


def test_returns(data):
    returns = data.returns
    assert isinstance(returns, pd.DataFrame)
    assert returns.columns.tolist() == ['AKRN', 'BANEP', 'LKOH', 'PIKK', 'TTLK', CASH, PORTFOLIO]
    assert returns.index[-1] == pd.Timestamp('2018-10-15')
    assert returns.loc['2018-10-15', 'AKRN'] == pytest.approx(0.0)
    assert returns.loc['2018-09-15', 'BANEP'] == pytest.approx(0.03523558872878201)
    assert returns.loc['2018-08-15', 'LKOH'] == pytest.approx(0.02503703228893662)
    assert returns.loc['2018-07-15', 'PIKK'] == pytest.approx(0.019395259757738658)
    assert returns.loc['2018-06-15', 'TTLK'] == pytest.approx(-0.09084647277357231)
    assert returns.loc['2018-05-15', CASH] == pytest.approx(0.0)
    assert returns.loc['2018-10-15', PORTFOLIO] == pytest.approx(0.018324295493612242)


def test_decay(data):
    assert data.decay == 1 - 1 / model.PARAMS['data']['ew_lags']


def test_mean(data):
    mean = data.mean
    manager = ReturnsMLDataManager(tuple(sorted(POSITIONS)), pd.Timestamp(DATE))
    assert mean.iloc[:-2].equals(manager.value.prediction_mean)
    assert mean.iloc[-2] == 0
    assert mean.iloc[-1] == pytest.approx(0.011457986912775303)


def test_std(data):
    std = data.std
    manager = ReturnsMLDataManager(tuple(sorted(POSITIONS)), pd.Timestamp(DATE))
    assert np.allclose(std.iloc[:-2], manager.value.prediction_std)
    assert std.iloc[-2] == 0
    assert std.iloc[-1] == pytest.approx(0.03824804495891518)


def test_beta(data):
    beta = data.beta
    assert isinstance(beta, pd.Series)
    assert beta.shape == (7,)
    assert beta['AKRN'] == pytest.approx(0.989810061080618)
    assert beta['BANEP'] == pytest.approx(1.22122096024645)
    assert beta['LKOH'] == pytest.approx(1.04869998948027)
    assert beta['PIKK'] == pytest.approx(0.506707191185518)
    assert beta['TTLK'] == pytest.approx(0.895880185589862)
    assert beta[CASH] == pytest.approx(0.0)
    assert beta[PORTFOLIO] == pytest.approx(1.0)
    assert (beta * data._portfolio.weight).iloc[:-1].sum() == pytest.approx(1.0)


def test_str(data, capsys):
    print(data)
    captured = capsys.readouterr()
    assert 'Средняя корреляция - 32.88%' in captured.out
