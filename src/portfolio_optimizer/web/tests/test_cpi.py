import pytest

from portfolio_optimizer.web.web_cpi import cpi

CHECK_POINTS = [('1991-01-31', 1.0620),
                ('2018-01-31', 1.0031)]


@pytest.mark.parametrize('date, value', CHECK_POINTS)
def test_cpi(date, value):
    df = cpi()
    assert df[date] == value
