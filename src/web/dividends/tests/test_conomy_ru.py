import pandas as pd
import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox import options

from web.dividends import conomy_ru


def test_date_parser():
    assert conomy_ru.date_parser('-') is None
    assert conomy_ru.date_parser('30.11.2018 (рек.)') == pd.Timestamp('2018-11-30')
    assert conomy_ru.date_parser('19.07.2017') == pd.Timestamp('2017-07-19')


def test_div_parser():
    assert conomy_ru.div_parser('2.23') == 2.23
    assert conomy_ru.div_parser('30,4') == 30.4
    assert conomy_ru.div_parser('4') == 4
    assert conomy_ru.div_parser('66.8 (рек.)') == 66.8
    assert conomy_ru.div_parser('78,9 (прогноз)') == 78.9
    assert conomy_ru.div_parser('-') == 0.0


def test_xpath_await():
    driver_options = options.Options()
    driver_options.headless = True
    with webdriver.Firefox(options=driver_options) as driver:
        driver.get(conomy_ru.SEARCH_URL)
        element = conomy_ru.xpath_await(driver, conomy_ru.SEARCH_FIELD)
        assert element.get_attribute('placeholder') == 'Поиск эмитентов по названию или тикеру'


def test_xpath_await_no_element():
    driver_options = options.Options()
    driver_options.headless = True
    with webdriver.Firefox(options=driver_options) as driver, pytest.raises(TimeoutException) as error:
        driver.get(conomy_ru.SEARCH_URL)
        conomy_ru.xpath_await(driver, conomy_ru.SEARCH_FIELD + '/div', 1)
    assert error.type == TimeoutException


def test_load_ticker_page():
    driver_options = options.Options()
    driver_options.headless = True
    with webdriver.Firefox(options=driver_options) as driver:
        conomy_ru.load_ticker_page(driver, 'AKRN')
        conomy_ru.xpath_await(driver, conomy_ru.DIVIDENDS_MENU)
        assert driver.current_url == 'https://www.conomy.ru/emitent/akron'


def test_load_dividends_table():
    driver_options = options.Options()
    driver_options.headless = True
    with webdriver.Firefox(options=driver_options) as driver:
        driver.get('https://www.conomy.ru/emitent/akron')
        conomy_ru.load_dividends_table(driver)
        assert driver.current_url == 'https://www.conomy.ru/emitent/akron/akrn-div'


def test_get_html():
    assert 'размер выплачиваемых ОАО «Акрон» дивидендов должен' in conomy_ru.get_html('AKRN')


def test_is_common():
    assert conomy_ru.is_common('CHMF')
    assert not conomy_ru.is_common('SNGSP')
    with pytest.raises(ValueError) as error:
        conomy_ru.is_common('TANGO')
    assert str(error.value) == 'Некорректный тикер TANGO'


def test_dividends_conomy_common():
    df = conomy_ru.dividends_conomy('SBER')
    assert isinstance(df, pd.Series)
    assert df.size >= 9
    assert df.index[0] == pd.Timestamp('2010-04-16')
    assert df['2011-04-15'] == 0.92


def test_dividends_conomy_preferred():
    df = conomy_ru.dividends_conomy('SBERP')
    assert isinstance(df, pd.Series)
    assert df.size >= 9
    assert df.index[0] == pd.Timestamp('2010-04-16')
    assert df['2012-04-12'] == 2.59
