import urllib.error

import pytest

from web.dividends.dohod_ru import dividends_dohod, make_url


def test_url():
    assert make_url('MOEX') == 'http://www.dohod.ru/ik/analytics/dividend/moex'


def test_wrong_url():
    with pytest.raises(urllib.error.URLError) as info:
        dividends_dohod('TEST')
    url = make_url('TEST')
    assert f'Неверный url: {url}' in str(info.value)


def test_get_dividends():
    df = dividends_dohod('VSMO')
    assert df.loc['2017-10-19'] == 762.68
    assert df.loc['2004-03-29'] == 11


def test_no_dividends_table_in_html():
    with pytest.raises(IndexError) as error:
        dividends_dohod('MSRS')
    assert 'На странице нет таблицы 2' == str(error.value)
