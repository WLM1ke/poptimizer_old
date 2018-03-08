import datetime

from ..loader_dividends import get_ticker_dividends, Dividends


class TestDividends():
    def test_df(self):
        div = Dividends('AKRN')
        assert div._html is None
        assert div._html != div.html
        assert div._html is not None


def test_get_dividends():
    assert get_ticker_dividends('CHMF').loc[datetime.date(2017, 9, 26), 'DIVIDENDS'] == '22.28'
