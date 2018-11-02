import pandas as pd
import pytest

from web.dividends import conomy_ru
from web.dividends import parser

HTML = """
        <table>
          <tbody>
          <tr>
            <td rowspan=2> 1,1</td>
            <td> 2.2</td>
            <td rowspan=2 colspan=2> 3</td>
            <td rowspan=3> 4 (рек)</td>
          </tr>
          <tr>
            <td> 5.55 (сов)</td>
          </tr>
          <tr>
            <td> 66,6 пред</td>
            <td colspan=3> 7</td>
          </tr>
          </tbody>
        </table>
        <table>
          <tr>
            <td rowspan=2>1,1</td>
            <td>2.2</td>
            <td rowspan=2 colspan=2>3</td>
            <td rowspan=3>4 (рек)</td>
          </tr>
          <tr>
            <td>5.55 (сов)</td>
          </tr>
          <tr>
            <td>66,6 пред</td>
            <td colspan=3>7</td>
          </tr>
        </table>
       """

RESULT0 = [[' 1,1', ' 2.2', ' 3', ' 3', ' 4 (рек)'],
           [' 1,1', ' 5.55 (сов)', ' 3', ' 3', ' 4 (рек)'],
           [' 66,6 пред', ' 7', ' 7', ' 7', ' 4 (рек)']]

RESULT1 = [['1,1', '2.2', '3', '3', '4 (рек)'],
           ['1,1', '5.55 (сов)', '3', '3', '4 (рек)'],
           ['66,6 пред', '7', '7', '7', '4 (рек)']]

DF_DATA = [[1.1, 2.2, 3.0, 3.0, 4.0],
           [1.1, 5.55, 3.0, 3.0, 4.0],
           [66.6, 7.0, 7.0, 7.0, 4.0]]


def test_parse_tbody():
    table = parser.HTMLTableParser(HTML, 0)
    assert table.parsed_table == RESULT0


def test_parse_no_tbody():
    table = parser.HTMLTableParser(HTML, 1)
    assert table.parsed_table == RESULT1


def test_no_table():
    with pytest.raises(IndexError) as error:
        parser.HTMLTableParser(HTML, 2)
        assert error.value == 'На странице нет таблицы 2'


def test_fast_second_parse():
    table = parser.HTMLTableParser(HTML, 1)
    assert table.parsed_table == RESULT1
    assert table.parsed_table == RESULT1


def test_make_df():
    table = parser.HTMLTableParser(HTML, 1)
    columns = [parser.DataColumn(i, {}, lambda x: x) for i in range(5)]
    df = pd.DataFrame(RESULT1)
    assert df.equals(table.make_df(columns))


def test_make_df_with_parsed_data():
    table = parser.HTMLTableParser(HTML, 1)
    columns = [parser.DataColumn(i, {}, conomy_ru.div_parser) for i in range(5)]
    df = pd.DataFrame(DF_DATA)
    assert df.equals(table.make_df(columns))


def test_make_df_drop():
    table = parser.HTMLTableParser(HTML, 1)
    columns = [parser.DataColumn(i, {}, conomy_ru.div_parser) for i in range(5)]
    df = pd.DataFrame(DF_DATA[1:2])
    assert df.equals(table.make_df(columns, 1, 1))


def test_make_df_validate():
    table = parser.HTMLTableParser(HTML, 1)
    columns = [parser.DataColumn(i, {0: RESULT1[0][i]}, conomy_ru.div_parser) for i in range(5)]
    df = pd.DataFrame(DF_DATA[1:])
    assert df.equals(table.make_df(columns, 1))


def test_make_df_fail_validate():
    table = parser.HTMLTableParser(HTML, 1)
    columns = [parser.DataColumn(1, {0: '2.2', 1: 'test'}, lambda x: x)]
    with pytest.raises(ValueError) as error:
        table.make_df(columns)
        assert error.value == 'Значение в таблице "5.55 (сов)" - должно быть "test"'
