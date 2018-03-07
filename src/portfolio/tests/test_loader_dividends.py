import datetime

from ..loader_dividends import Dividends


class TestDividends():
    def test_df(self):
        div = Dividends('CHMF')
        assert div._html is None
        assert div._html != div.html
        assert div._html is not None
        assert div.df.loc[datetime.date(2017, 9, 26), 'DIVIDENDS'] == '22.28'
