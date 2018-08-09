import pytest

import optimizer
import portfolio
from optimizer import Optimizer
from portfolio import Portfolio
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
    save_cut_off = portfolio.VOLUME_CUT_OFF
    # Все кейсы составлены для константы ограничения на объем 0.0024 * 0.7
    portfolio.VOLUME_CUT_OFF = 0.024 * 0.7
    opt = Optimizer(port)
    yield opt
    portfolio.VOLUME_CUT_OFF = save_cut_off


def test_dividends_gradient_growth(opt):
    gradient_growth = opt.dividends_gradient_growth
    assert gradient_growth['MSTT'] == pytest.approx(0.0150019046805012 * AFTER_TAX)
    assert gradient_growth['MSRS'] == pytest.approx(0.0060675423458529 * AFTER_TAX)
    assert gradient_growth['RTKMP'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['LSNGP'] == pytest.approx(0.0129806845953583 * AFTER_TAX)
    assert gradient_growth['LKOH'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['PMSBP'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['CHMF'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['GMKN'] == pytest.approx(0.0000103831583048243 * AFTER_TAX)


def test_drawdown_gradient_growth(opt):
    gradient_growth = opt.drawdown_gradient_growth
    assert gradient_growth['MSTT'] == pytest.approx(0.401649945393276)
    assert gradient_growth['MSRS'] == pytest.approx(0.0332388067600244)
    assert gradient_growth['RTKMP'] == pytest.approx(0.0)
    assert gradient_growth['LSNGP'] == pytest.approx(0.0520475277822001)
    assert gradient_growth['LKOH'] == pytest.approx(0.0)
    assert gradient_growth['PMSBP'] == pytest.approx(0.0)
    assert gradient_growth['CHMF'] == pytest.approx(0.0)
    assert gradient_growth['GMKN'] == pytest.approx(0.0321441209442009)


def test_dominated(opt):
    dominated = opt.dominated
    assert dominated['UPRO'] == 'VSMO'
    assert dominated['LSRG'] == ''
    assert dominated['VSMO'] == ''
    assert dominated['SNGSP'] == 'CHMF'


def test_t_dividends_growth(opt):
    assert opt.t_dividends_growth == pytest.approx(0.615029013474924)


def test_t_drawdown_growth(opt):
    assert opt.t_drawdown_growth == pytest.approx(2.23435983550963)


def test_best_trade(opt):
    best_string = opt._str_best_trade()
    assert 'Продать MSTT - 5 сделок по 19 лотов' in best_string
    assert 'Купить LSRG - 5 сделок по 26 лотов' in best_string


def test_str_t_score_10(opt, monkeypatch):
    monkeypatch.setattr(optimizer, 'T_SCORE', 10.0)
    report = str(opt)
    assert 'ОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ' in report
    t_score = 2.23435983550963
    assert f'Прирост просадки составляет {t_score:.2f} СКО < 10.00' in report


def test_str_t_score(opt):
    report = str(opt)
    assert 'ОПТИМИЗАЦИЯ ТРЕБУЕТСЯ' in report
    t_score = 2.23435983550963
    assert f'Прирост просадки составляет {t_score:.2f} СКО > 2.00' in report


def test_str_dividends(opt, monkeypatch):
    monkeypatch.setattr(Optimizer, 't_drawdown_growth', 0)
    report = str(opt)
    assert 'ОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ' in report
    t_score = 0.615029013474924
    assert f'Прирост дивидендов составляет {t_score:.2f} СКО < 2.00' in report
