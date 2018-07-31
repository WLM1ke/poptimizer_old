from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from web import web_dividends_smart_lab
from web.labels import DIVIDENDS, TICKER


@pytest.fixture(scope='module', autouse=True)
def fake_get_html_table():
    saved_get_html_table = web_dividends_smart_lab.get_html_table
    with open(Path(__file__).parent / 'data' / 'test_table.html') as file:
        html_table = file.read()
    web_dividends_smart_lab.get_html_table = lambda url, table_index: BeautifulSoup(html_table, 'lxml')
    yield
    web_dividends_smart_lab.get_html_table = saved_get_html_table


def test_dividends_smart_lab():
    df = web_dividends_smart_lab.dividends_smart_lab()
    assert df.shape == (1, 2)
    assert '2018-09-25' in df.index
    assert df.loc['2018-09-25', TICKER] == 'CHMF'
    assert df.loc['2018-09-25', DIVIDENDS] == 45.94
