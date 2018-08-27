import pytest

from metrics.dividends_metrics_base import BaseDividendsMetrics
from metrics.portfolio import CASH, PORTFOLIO, Portfolio
from settings import AFTER_TAX


@pytest.fixture(scope='module', name='div')
def case_metrics():
    positions = dict(AKRN=679,
                     GMKN=139,
                     LSRG=172,
                     MSTT=2436,
                     TTLK=234)
    port = Portfolio(date='2018-05-11',
                     cash=311_587,
                     positions=positions)
    return BaseDividendsMetrics(port)


def test_mean(div):
    mean = div.mean
    assert mean['AKRN'] / AFTER_TAX == pytest.approx(0.0540386666639274)
    assert mean[CASH] / AFTER_TAX == pytest.approx(0)
    assert mean[PORTFOLIO] / AFTER_TAX == pytest.approx(0.071162452199256)


def test_std(div):
    mean = div.std
    assert mean['GMKN'] / AFTER_TAX == pytest.approx(0.0431225878430593)
    assert mean[CASH] / AFTER_TAX == pytest.approx(0)
    assert mean[PORTFOLIO] / AFTER_TAX == pytest.approx(0.0208019150227195)


def test_beta(div):
    mean = div.beta
    assert mean['LSRG'] == pytest.approx(0.209672686516287)
    assert mean[CASH] == pytest.approx(0)
    assert mean[PORTFOLIO] == pytest.approx(1)


def test_lower_bound(div):
    mean = div.lower_bound
    assert mean['MSTT'] / AFTER_TAX == pytest.approx(0.0234615502317854)
    assert mean[CASH] / AFTER_TAX == pytest.approx(0.0)
    assert mean[PORTFOLIO] / AFTER_TAX == pytest.approx(0.0295586221538169)


def test_gradient_of_lower_bound(div):
    mean = div.gradient
    assert mean['TTLK'] / AFTER_TAX == pytest.approx(0.000617979982047365)
    assert mean[CASH] / AFTER_TAX == pytest.approx(-0.0295586221538169)
    assert mean[PORTFOLIO] / AFTER_TAX == pytest.approx(0)


def test_str(div):
    text = str(div)
    assert 'КЛЮЧЕВЫЕ МЕТРИКИ ДИВИДЕНДОВ' in text
    assert 'MEAN' in text
    assert 'STD' in text
    assert 'BETA' in text
    assert 'LOWER_BOUND' in text
    assert 'GRADIENT' in text


def test_end_of_month_shape():
    positions = dict(AKRN=679,
                     GMKN=139,
                     LSRG=172,
                     MSTT=2436,
                     TTLK=234)
    port = Portfolio(date='2018-07-30',
                     cash=311_587,
                     positions=positions)
    return BaseDividendsMetrics(port).real_after_tax.shape == (5, 7)
