import pytest

from metrics import portfolio, returns_metrics_base
from metrics.portfolio import CASH, PORTFOLIO


@pytest.fixture(scope='module', name='returns')
def case_metrics():
    positions = dict(MSTT=4650,
                     LSNGP=162,
                     MTSS=749,
                     AKRN=795,
                     GMKN=223)
    port = portfolio.Portfolio(date='2018-03-19',
                               cash=1_415_988,
                               positions=positions)
    return returns_metrics_base.BaseReturnsMetrics(port)


def test_decay(returns):
    assert returns.decay == pytest.approx(0.87297494460045133)


def test_mean(returns):
    returns._decay = 0.89
    mean = returns.mean
    assert mean['AKRN'] == pytest.approx(0.0211622465241811)
    assert mean[CASH] == pytest.approx(0.0)
    assert mean[PORTFOLIO] == pytest.approx(0.0243328461575859)


def test_std(returns):
    returns._decay = 0.90
    std = returns.std
    # В xls рассчитываются смещенные оценки - для сопоставимости нужна поправка
    bias = std[PORTFOLIO] / returns.returns.ewm(alpha=1 - returns.decay).std(bias=True).iloc[-1][PORTFOLIO]
    assert std['LSNGP'] == pytest.approx(0.128921045645328 * bias)
    assert std[CASH] == pytest.approx(0.0 * bias)
    assert std[PORTFOLIO] == pytest.approx(0.0402893148874336 * bias)


def test_beta(returns):
    returns._decay = 0.91
    beta = returns.beta
    assert beta['GMKN'] == pytest.approx(0.686600110203995)
    assert beta[CASH] == pytest.approx(0.0)
    assert beta[PORTFOLIO] == pytest.approx(1.0)


def test_draw_down(returns):
    returns._decay = 0.92
    draw_down = returns.draw_down
    # В xls рассчитываются смещенные оценки - для сопоставимости нужна поправка в квадрате
    bias = returns.std[PORTFOLIO] / returns.returns.ewm(alpha=1 - returns.decay).std(bias=True).iloc[-1][PORTFOLIO]
    bias = bias ** 2
    assert draw_down['MSTT'] == pytest.approx(-0.225773776260828 * bias)
    assert draw_down[CASH] == pytest.approx(0.0 * bias)
    assert draw_down[PORTFOLIO] == pytest.approx(-0.0733527897934848 * bias)


def test_gradient(returns):
    returns._decay = 0.93
    gradient = returns.gradient
    # В xls рассчитываются смещенные оценки - для сопоставимости нужна поправка в квадрате
    bias = returns.std[PORTFOLIO] / returns.returns.ewm(alpha=1 - returns.decay).std(bias=True).iloc[-1][PORTFOLIO]
    bias = bias ** 2
    assert gradient['MTSS'] == pytest.approx(0.00251871848426797 * bias)
    assert gradient[CASH] == pytest.approx(0.0784652929454137 * bias)
    assert gradient[PORTFOLIO] == pytest.approx(0.0 * bias)


def test_str(returns):
    text = str(returns)
    assert 'КЛЮЧЕВЫЕ МЕТРИКИ ДОХОДНОСТИ' in text
    assert 'MEAN' in text
    assert 'STD' in text
    assert 'BETA' in text
    assert 'DRAW_DOWN' in text
    assert 'GRADIENT' in text


def test_time_to_draw_down(returns):
    assert returns.time_to_draw_down == pytest.approx(3.67737965394373)


def test_std_at_draw_down(returns):
    assert returns.std_at_draw_down == pytest.approx(0.0814183042618772)
