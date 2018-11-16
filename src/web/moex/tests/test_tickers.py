import pytest

from web.moex.iss_tickers import reg_number_tickers

check_points = [('1-02-65104-D', ('UPRO', 'EONR', 'OGK4')),
                ('10301481B', ('SBER', 'SBER03')),
                ('20301481B', ('SBERP', 'SBERP03')),
                ('1-02-06556-A', ('PHOR',))]


@pytest.mark.parametrize("reg_number, expected", check_points)
def test_reg_number_tickers(reg_number, expected):
    assert reg_number_tickers(reg_number) == expected
