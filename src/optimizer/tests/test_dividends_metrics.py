import pytest

from optimizer import dividends_metrics
from optimizer.settings import AFTER_TAX, CASH, PORTFOLIO


@pytest.fixture(scope='module', name='div')
def case_metrics():
    positions = dict(MSTT=8650,
                     RTKMP=1826,
                     UPRO=3370,
                     LKOH=2230,
                     MVID=3260)
    port = dividends_metrics.Portfolio(date='2018-03-19',
                                       cash=7_079_940,
                                       positions=positions)
    return dividends_metrics.DividendsMetrics(port, 2012, 2016)


def test_mean(div):
    mean = div.mean
    assert mean['MSTT'] / AFTER_TAX == pytest.approx(0.0687221899610839)
    assert mean[CASH] / AFTER_TAX == pytest.approx(0)
    assert mean[PORTFOLIO] / AFTER_TAX == pytest.approx(0.0726005495463236)


def test_std(div):
    mean = div.std
    assert mean['MVID'] / AFTER_TAX == pytest.approx(0.0592200339190128)
    assert mean[CASH] / AFTER_TAX == pytest.approx(0)
    assert mean[PORTFOLIO] / AFTER_TAX == pytest.approx(0.0145500209766352)


def test_beta(div):
    mean = div.beta
    assert mean['UPRO'] == pytest.approx(1.49810323257627)
    assert mean[CASH] == pytest.approx(0)
    assert mean[PORTFOLIO] == pytest.approx(1)


def test_lower_bound(div):
    mean = div.lower_bound
    assert mean['RTKMP'] / AFTER_TAX == pytest.approx(0.0709883190432636)
    assert mean[CASH] / AFTER_TAX == pytest.approx(0.0)
    assert mean[PORTFOLIO] / AFTER_TAX == pytest.approx(0.0435005075930532)


def test_gradient_of_lower_bound(div):
    mean = div.gradient_of_lower_bound
    assert mean['LKOH'] / AFTER_TAX == pytest.approx(-0.000722104546789663)
    assert mean[CASH] / AFTER_TAX == pytest.approx(-0.0435005075930532)
    assert mean[PORTFOLIO] / AFTER_TAX == pytest.approx(0)


def test_str(div):
    text = str(div)
    assert 'Ключевые метрики дивидендов:' in text
    assert 'MEAN' in text
    assert 'STD' in text
    assert 'BETA' in text
    assert 'LOWER_BOUND' in text
    assert 'GRADIENT' in text
