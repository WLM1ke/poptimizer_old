from pathlib import Path

import pytest

import local.local_legacy_dividends
import optimizer
import portfolio
from optimizer import Optimizer
from portfolio import Portfolio, CASH, PORTFOLIO
from settings import AFTER_TAX


@pytest.fixture(scope='module', autouse=True)
def fake_legacy_dividends():
    saved_path = local.local_legacy_dividends.FILE_PATH
    fake_path = Path(__file__).parent.parent / 'local' / 'tests' / 'data' / 'dividends.xlsx'
    local.local_legacy_dividends.FILE_PATH = fake_path
    yield
    local.local_legacy_dividends.FILE_PATH = saved_path


@pytest.fixture(scope='module', name='opt')
def case_optimizer():
    pos = dict(BANEP=0,
               MFON=55,
               SNGSP=31,
               RTKM=0,
               MAGN=0,
               MSTT=4650,
               KBTK=9,
               MOEX=0,
               RTKMP=1826,
               NMTP=0,
               TTLK=0,
               LSRG=641,
               LSNGP=81,
               PRTK=119,
               MTSS=749,
               AKRN=795,
               MRKC=343,
               GAZP=0,
               AFLT=5,
               MSRS=699,
               UPRO=1267,
               PMSBP=682,
               CHMF=55,
               GMKN=223,
               VSMO=145,
               RSTIP=265,
               PHOR=0,
               MRSB=23,
               LKOH=123,
               ENRU=467,
               MVID=326)
    port = Portfolio(date='2018-02-19',
                     cash=0 + 2749.64 + 4330.3,
                     positions=pos)
    save_cut_off = portfolio.VOLUME_CUT_OFF
    # Все кейсы составлены для константы ограничения на объем 0.0024
    portfolio.VOLUME_CUT_OFF = 0.0024
    opt = Optimizer(port)
    # Все кейсы составлены для константы сглаживания 0.9
    opt.returns_metrics._decay = 0.9

    yield opt
    portfolio.VOLUME_CUT_OFF = save_cut_off


def test_gradient_growth(opt):
    gradient_growth = opt.dividends_gradient_growth
    assert gradient_growth['VSMO'] == pytest.approx(0.00912015113393044 * AFTER_TAX)
    assert gradient_growth['MSRS'] == pytest.approx(0.00201127964982818 * AFTER_TAX)
    assert gradient_growth['ENRU'] == pytest.approx(0.00155403975015344 * AFTER_TAX)
    assert gradient_growth['LSNGP'] == pytest.approx(0.00955869568790973 * AFTER_TAX)
    assert gradient_growth['LKOH'] == pytest.approx(0.0165442768681765 * AFTER_TAX)
    assert gradient_growth['GAZP'] == pytest.approx(0.0 * AFTER_TAX)
    assert gradient_growth['CHMF'] == pytest.approx(0.013808089777053 * AFTER_TAX)
    assert gradient_growth['PRTK'] == pytest.approx(0.0274781708822527 * AFTER_TAX)


def test_dominated(opt):
    dominated = opt.dominated
    assert dominated['UPRO'] == 'LSRG'
    assert dominated['LSRG'] == ''
    assert dominated['GAZP'] == ''
    assert dominated['MRKC'] == 'TTLK'


def adjustment(optimum):
    adj = (optimum.portfolio.weight[[CASH, PORTFOLIO]] * optimum.dividends_gradient_growth[[CASH, PORTFOLIO]]).sum()
    return adj / optimum.dividends_metrics.std[PORTFOLIO]


def test_t_growth(opt):
    # Для сопоставимости нужно добавить кэш и портфель
    assert opt.t_dividends_growth == pytest.approx(1.36317493495405 + adjustment(opt))


def test_best_trade(opt):
    best_string = opt.best_trade
    assert 'Продать PRTK - 5 сделок по 8 лотов' in best_string
    assert 'Купить MVID - 5 сделок по 0 лотов' in best_string


def test_str(opt, monkeypatch):
    monkeypatch.setattr(optimizer, 'T_SCORE', 10.0)
    report = str(opt)
    assert 'ОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ' in report
    t_score = 2.3070272135803465
    assert f'Прирост просадки составляет {t_score:.2f} СКО < 10.00' in report


def test_str_t_score_1(opt):
    report = str(opt)
    assert 'ОПТИМИЗАЦИЯ ТРЕБУЕТСЯ' in report
    t_score = 2.3070272135803465
    assert f'Прирост просадки составляет {t_score:.2f} СКО > 2.00' in report


def test_str_dividends(opt, monkeypatch):
    # Для сопоставимости нужно добавить кэш и портфель
    monkeypatch.setattr(Optimizer, 't_drawdown_growth', 0)
    report = str(opt)
    assert 'ОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ' in report
    t_score = 1.36317493495405 + adjustment(opt)
    assert f'Прирост дивидендов составляет {t_score:.2f} СКО < 2.00' in report
