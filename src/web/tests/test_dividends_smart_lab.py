from pathlib import Path

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from web import web_dividends_smart_lab
from web.labels import DATE, DIVIDENDS


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
    assert 'CHMF' in df.index
    assert df.loc['CHMF', DATE] == pd.Timestamp('2018-09-25')
    assert df.loc['CHMF', DIVIDENDS] == 45.94
