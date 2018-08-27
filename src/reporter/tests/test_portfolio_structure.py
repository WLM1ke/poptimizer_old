import pytest

from metrics.portfolio import PORTFOLIO, Portfolio
from reporter.portfolio_structure import drop_small_positions, MAX_TABLE_ROWS, OTHER, make_list_of_lists_table

POSITIONS = dict(BANEP=200,
                 MFON=55,
                 SNGSP=235,
                 RTKM=0,
                 MAGN=0,
                 MSTT=4435,
                 KBTK=9,
                 MOEX=0,
                 RTKMP=1475 + 312 + 39,
                 NMTP=0,
                 TTLK=0,
                 LSRG=561 + 0 + 80,
                 LSNGP=81,
                 PRTK=70,
                 MTSS=749,
                 AKRN=795,
                 MRKC=0 + 0 + 36,
                 GAZP=0,
                 AFLT=0,
                 MSRS=699,
                 UPRO=1267,
                 PMSBP=1188 + 322 + 219,
                 CHMF=0,
                 GMKN=166 + 28,
                 VSMO=73,
                 RSTIP=87,
                 PHOR=0,
                 MRSB=0,
                 LKOH=123,
                 ENRU=319 + 148,
                 MVID=264 + 62)
CASH = 596_156 + 470_259 + 481_849
DATE = '2018-04-19'
TEST_PORTFOLIO = Portfolio(date=DATE,
                           cash=CASH,
                           positions=POSITIONS)


def test_drop_small_positions():
    df = drop_small_positions(TEST_PORTFOLIO)
    index = df.index
    assert len(df) == MAX_TABLE_ROWS + 2
    assert index[-1] == PORTFOLIO
    assert df[PORTFOLIO] == pytest.approx(39226178)
    assert index[-2] == OTHER
    assert df[OTHER] == pytest.approx(6523354)
    assert index[0] == 'RTKMP'
    assert df.iloc[0] == pytest.approx(11167816)
    assert index[-3] == 'MVID'
    assert df.iloc[-3] == pytest.approx(1310520)


def test_make_list_of_lists_table():
    list_of_lists = make_list_of_lists_table(TEST_PORTFOLIO)
    assert len(list_of_lists) == MAX_TABLE_ROWS + 3
    assert list_of_lists[0] == ['Name', 'Value', 'Share']
    assert list_of_lists[-1] == ['PORTFOLIO', '39 226 178', '100.0%']
    assert list_of_lists[7] == ['CASH', '1 548 264', '3.9%']
    assert list_of_lists[5] == ['MTSS', '2 168 355', '5.5%']
