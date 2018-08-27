import pandas as pd
import pytest

import momentum_tickers
from metrics.portfolio import CASH, Portfolio
from momentum_tickers import all_securities, all_securities_with_reg_number
from momentum_tickers import non_portfolio_securities, make_new_portfolio, valid_volume
from momentum_tickers import valid_return_gradient
from web.labels import REG_NUMBER


@pytest.fixture(scope='module', autouse=True, name='port')
def make_test_portfolio():
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123))
    return port


def test_all_securities():
    df = all_securities()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 200
    assert df.index[0] == 'ABBN'
    assert df[REG_NUMBER].iat[0] is None
    assert df.index[-1] == 'ZVEZ'
    assert df[REG_NUMBER].iat[-1] == '1-01-00169-D'
    assert 'YNDX' in df.index


def test_all_securities_with_reg_number():
    tickers_set = all_securities_with_reg_number()
    assert 'ABBN' not in tickers_set
    assert 'YNDX' not in tickers_set
    assert 'ABRD' in tickers_set
    assert 'AKRN' in tickers_set
    assert 'ZVEZ' in tickers_set
    assert 'CHMF' in tickers_set
    assert 'GAZP' in tickers_set
    assert 'VSMO' in tickers_set
    assert 'TTLK' in tickers_set


def test_non_portfolio_securities(port):
    tickers_list = non_portfolio_securities(port)
    assert 'ABBN' not in tickers_list
    assert 'YNDX' not in tickers_list
    assert 'ABRD' in tickers_list
    assert 'AKRN' in tickers_list
    assert 'ZVEZ' in tickers_list
    assert 'CHMF' in tickers_list
    assert 'GAZP' not in tickers_list
    assert 'VSMO' not in tickers_list
    assert 'TTLK' not in tickers_list


def test_make_new_portfolio(port):
    new_port = make_new_portfolio(port, 'AKRN')
    assert isinstance(new_port, Portfolio)
    assert 'AKRN' in new_port.positions
    assert 'GAZP' in new_port.positions
    assert 'VSMO' in new_port.positions
    assert 'TTLK' in new_port.positions
    assert len(new_port.positions) == 6
    assert new_port.date == pd.Timestamp('2018-03-19').date()
    assert new_port.lots[CASH] == pytest.approx(1000.21)
    assert new_port.lots['AKRN'] == pytest.approx(0)
    assert new_port.lots['VSMO'] == pytest.approx(145)
    assert new_port.lots['TTLK'] == pytest.approx(123)
    assert new_port.lots['GAZP'] == pytest.approx(682)


def test_valid_volume(port):
    assert valid_volume(port, 'GAZP')
    assert valid_volume(port, 'VSMO')
    assert not valid_volume(port, 'TTLK')
    assert not valid_volume(make_new_portfolio(port, 'KRSB'), 'KRSB')


def test_valid_return_gradient(port):
    assert not valid_return_gradient(port, 'TTLK', 2)
    assert not valid_return_gradient(port, 'GAZP', 2)
    assert not valid_return_gradient(port, 'VSMO', 0)
    assert valid_return_gradient(port, 'TTLK', -1)


TICKER_CASES = ['ARSA', 'SNGSP', 'ALNU']


@pytest.mark.parametrize('cases', TICKER_CASES)
def test_find_momentum_tickers(port, capsys, monkeypatch, cases):
    monkeypatch.setattr(momentum_tickers, 'non_portfolio_securities', lambda x: [cases])
    momentum_tickers.find_momentum_tickers(port, 1.73)
    captured_string = capsys.readouterr().out
    assert '1. ' in captured_string
    assert ((' 1.73 СКО' in captured_string) or
            ('Фактор оборота                                                          0.0000' in captured_string))
