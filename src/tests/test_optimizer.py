import pytest

import optimizer
from metrics import portfolio
from metrics.portfolio import Portfolio
from optimizer import Optimizer
from settings import AFTER_TAX


@pytest.fixture(scope='module', name='opt')
def case_optimizer():
    pos = dict(AKRN=679,
               BANEP=392,
               CHMF=173,
               GMKN=139,
               LKOH=123,
               LSNGP=59,
               LSRG=1341,
               MSRS=38,
               MSTT=2181,
               MTSS=1264,
               MVID=141,
               PMSBP=2715,
               RTKMP=1674,
               SNGSP=263,
               TTLK=234,
               UPRO=1272,
               VSMO=101)
    port = Portfolio(date='2018-07-24',
                     cash=102_262,
                     positions=pos)
    save_max_trade = optimizer.MAX_TRADE
    save_cut_off = portfolio.VOLUME_CUT_OFF
    save_dividends_metrics = optimizer.DIVIDENDS_METRICS
    optimizer.MAX_TRADE = 0.006
    portfolio.VOLUME_CUT_OFF = 2.9 * optimizer.MAX_TRADE
    optimizer.DIVIDENDS_METRICS = 'BaseDividendsMetrics'
    opt = Optimizer(port)
    yield opt
    optimizer.MAX_TRADE = save_max_trade
    portfolio.VOLUME_CUT_OFF = save_cut_off
    optimizer.DIVIDENDS_METRICS = save_dividends_metrics


def test_dividends_gradient_growth(opt):
    gradient_growth = opt.dividends_gradient_growth
    assert gradient_growth['MSTT'] == pytest.approx(0.0150399027409569 * AFTER_TAX)
    assert gradient_growth['MSRS'] == pytest.approx(0.0060346499492693 * AFTER_TAX)
    assert gradient_growth['RTKMP'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['LSNGP'] == pytest.approx(0.0129893484990373 * AFTER_TAX)
    assert gradient_growth['LKOH'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['PMSBP'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['CHMF'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['GMKN'] == pytest.approx(0.0 * AFTER_TAX)


def test_drawdown_gradient_growth(opt):
    gradient_growth = opt.drawdown_gradient_growth
    assert gradient_growth['MSTT'] == pytest.approx(0.401214460511816)
    assert gradient_growth['MSRS'] == pytest.approx(0.0338249311250068)
    assert gradient_growth['RTKMP'] == pytest.approx(0.0)
    assert gradient_growth['LSNGP'] == pytest.approx(0.0508412824832902)
    assert gradient_growth['LKOH'] == pytest.approx(0.0)
    assert gradient_growth['PMSBP'] == pytest.approx(0.0)
    assert gradient_growth['CHMF'] == pytest.approx(0.0)
    assert gradient_growth['GMKN'] == pytest.approx(0.0)


def test_dominated(opt):
    dominated = opt.dominated
    assert dominated['UPRO'] == 'RTKMP'
    assert dominated['LSRG'] == ''
    assert dominated['VSMO'] == ''
    assert dominated['SNGSP'] == 'CHMF'


def test_t_dividends_growth(opt):
    assert opt.t_dividends_growth == pytest.approx(0.613956329529872)


def test_t_drawdown_growth(opt):
    assert opt.t_drawdown_growth == pytest.approx(0.472858179816854)


def test_best_trade(opt):
    best_string = opt._str_best_trade()
    assert 'Продать AKRN - 5 сделок по 5 лотов' in best_string
    assert 'Купить CHMF - 5 сделок по 2 лотов' in best_string


def test_str_t_score_10(opt, monkeypatch):
    monkeypatch.setattr(optimizer, 'T_SCORE', 10.0)
    report = str(opt)
    assert 'ОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ' in report
    t_dividends = 0.613956329529872
    t_return = 0.472858179816854
    assert f'Прирост дивидендов - {t_dividends:.2f} СКО' in report
    assert f'Прирост просадки - {t_return:.2f} СКО' in report


def test_str_t_score(opt, monkeypatch):
    monkeypatch.setattr(optimizer, 'T_SCORE', 0.4)
    report = str(opt)
    assert 'ОПТИМИЗАЦИЯ ТРЕБУЕТСЯ' in report
    t_dividends = 0.613956329529872
    t_return = 0.472858179816854
    assert f'Прирост дивидендов - {t_dividends:.2f} СКО' in report
    assert f'Прирост просадки - {t_return:.2f} СКО' in report


def test_cash_out(opt):
    assert 'Для вывода средств продать LSNGP - 5 сделок по 3 лотов' == opt.cash_out


def test_cash_out_enough(opt, monkeypatch):
    monkeypatch.setattr(optimizer, 'MAX_TRADE', 0.0)
    assert 'Средств достаточно для вывода' == opt.cash_out
