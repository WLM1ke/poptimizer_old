import pytest

from portfolio_optimizer.download.cpi import get_monthly_cpi

CHECK_POINTS = [('1991-01-31', 1.0620),
                ('2018-01-31', 1.0031)]


@pytest.mark.parametrize('date, cpi', CHECK_POINTS)
def test_get_monthly_cpi(date, cpi):
    df = get_monthly_cpi()
    assert df[date] == cpi
