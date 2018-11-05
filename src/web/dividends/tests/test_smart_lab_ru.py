import pytest

from web.dividends import smart_lab_ru
from web.labels import DIVIDENDS, TICKER

HTML = """
<table>
</table>
<table>
</table>
<table cellspacing="0" class="simple-little-table trades-table events moex_bonds_inline">
    <tr>
        <th><a class="active" href="/dividends/index/order_by_short_name/asc/">Название</a></th>
        <th><a href="/dividends/index/order_by_ticker/desc/">Тикер</a></th>
        <th class="chartrow"> </th>
        <th><a href="/dividends/index/order_by_t2_date/asc/">дата T-2</a></th>
        <th><a href="/dividends/index/order_by_cut_off_date/desc/">дата отсечки</a></th>
        <th>Год</th>
        <th>Период</th>
        <th><a href="/dividends/index/order_by_dividend/desc/">дивиденд,<br/>руб</a></th>
        <th>Цена акции</th>
        <th><a href="/dividends/index/order_by_yield/desc/">Див.<br/>доходность</a></th>
    </tr>
    <tr class="dividend_approved">
        <td><a href="/forum/%D0%A1%D0%B5%D0%B2%D0%B5%D1%80%D1%81%D1%82%D0%B0%D0%BB%D1%8C"
               title="Северсталь">СевСт-ао</a></td>
        <td>CHMF</td>
        <td><a class="charticon2" href="/q/CHMF/f/y/dividend/" target="_blank"
               title="Северсталь (CHMF) дивиденды история"></a></td>
        <td>
            21.09.2018
        </td>
        <td>
            25.09.2018
        </td>
        <td>2018</td>
        <td>
            2 кв
        </td>
        <td><strong>45,94</strong></td>
        <td>972,5</td>
        <td><strong>4,7%</strong></td>
    </tr>
    <tr>
        <td colspan="11" class="right">
        <div style="float: left;"><a href="/dividends/add/" style="font-weight: normal;">+добавить дивиденды</a></div>
        <a href="/dividends/history/">История выплаченных дивидендов</a>
        </td>
    </tr>
</table>"""


@pytest.fixture(scope='module', autouse=True)
def fake_get_html_table():
    saved_get_html = smart_lab_ru.dohod_ru.get_html
    smart_lab_ru.dohod_ru.get_html = lambda url: HTML
    yield
    smart_lab_ru.dohod_ru.get_html = saved_get_html


def test_dividends_smart_lab():
    df = smart_lab_ru.dividends_smart_lab()
    assert df.shape == (1, 2)
    assert '2018-09-25' in df.index
    assert df.loc['2018-09-25', TICKER] == 'CHMF'
    assert df.loc['2018-09-25', DIVIDENDS] == 45.94
