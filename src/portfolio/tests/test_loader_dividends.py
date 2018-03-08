import datetime
import urllib.error

import pytest

from ..loader_dividends import get_ticker_dividends, Dividends


class TestDividends:
    def test_url(self):
        assert Dividends('MOEX').url == 'http://www.dohod.ru/ik/analytics/dividend/moex'

    def test_wrong_url(self):
        with pytest.raises(urllib.error.URLError) as info:
            Dividends('TEST').html
        assert '<urlopen error Не верный url: http://www.dohod.ru/ik/analytics/dividend/test>' == str(info.value)

    def test_html_cache(self):
        div = Dividends('AKRN')
        assert div._html is None
        assert div._html != div.html
        assert div._html is not None


def test_get_dividends():
    assert get_ticker_dividends('CHMF').loc[datetime.date(2017, 9, 26), 'DIVIDENDS'] == 22.28
