import pandas as pd
import pytest

from portfolio_optimizer.portfolio import Portfolio
from portfolio_optimizer.settings import PORTFOLIO


def test_portfolio():
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123),
                     value=3_699_111.41)
    date = pd.to_datetime('2018-03-19').date()
    assert port.date == date
    assert f'Дата портфеля - {date}' in port.__str__()
    assert port.value[PORTFOLIO] == 3_699_111.41
    assert port.weight['VSMO'] == pytest.approx(0.691071)


def test_portfolio_change_date():
    port = Portfolio(date='2018-03-23',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123),
                     value=3_742_615.21)
    port.change_date('2018-03-19')
    date = pd.to_datetime('2018-03-19').date()
    assert port.date == date
    assert f'Дата портфеля - {date}' in port.__str__()
    assert port.value[PORTFOLIO] == 3_699_111.41
    assert port.weight['VSMO'] == pytest.approx(0.691071)


def test_portfolio_without_value():
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123))
    date = pd.to_datetime('2018-03-19').date()
    assert port.date == date
    assert f'Дата портфеля - {date}' in port.__str__()
    assert port.value[PORTFOLIO] == 3_699_111.41
    assert port.weight['VSMO'] == pytest.approx(0.691071)
