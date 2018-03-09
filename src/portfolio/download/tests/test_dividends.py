import datetime
import urllib.error

import pytest

from portfolio.download.dividends import get_dividends, make_url


def test_url():
    assert make_url('MOEX') == 'http://www.dohod.ru/ik/analytics/dividend/moex'


def test_wrong_url():
    with pytest.raises(urllib.error.URLError) as info:
        get_dividends('TEST')
    url = make_url('TEST')
    assert f'<urlopen error Неверный url: {url}>' == str(info.value)


def test_get_dividends():
    df = get_dividends('CHMF')
    assert df.loc[datetime.date(2017, 9, 26), 'DIVIDENDS'] == 22.28
    assert df.loc[datetime.date(2003, 5, 23), 'DIVIDENDS'] == 3
