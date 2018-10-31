"""Загрузка данных о дивидендах с https://www.conomy.ru/"""
import re

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox import options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import wait

# Время ожидания загрузки
from web.dividends.table_parser import AbstractTableParser, DataColumn
from web.labels import DATE

WAITING_TIME = 10

# Параметры поиска страницы эмитента
SEARCH_URL = 'https://www.conomy.ru/search'
SEARCH_FIELD = '//*[@id="issuer_search"]'

# Параметры поиска данных по дивидендам
DIVIDENDS_MENU = '//*[@id="page-wrapper"]/div/nav/ul/li[5]/a'
DIVIDENDS_TABLE = '//*[@id="page-container"]/div[2]/div/div[1]'

TABLE_INDEX = 1

ORDINARY = 'ORDINARY'
PREFERRED = 'PREFERRED'

# Параметры парсинга
NO_VALUE = '-'
DIV_PATTERN = r'.*\d'
DATE_PATTERN = r'\d{2}\.\d{2}\.\d{4}'


def xpath_await_find(driver, xpath: str, waiting_time: int = WAITING_TIME):
    """Ищет и возвращает элемент с заданным xpath

    При необходимости предварительно ждет загрузки в течении определенного количества секунд
    """
    load_wait = wait.WebDriverWait(driver, waiting_time)
    element_wait = expected_conditions.presence_of_element_located((By.XPATH, xpath))
    element = load_wait.until(element_wait)
    return element


def load_ticker_page(ticker: str, driver):
    """Вводит на страницу поиска тикер и переходит на страницу с информацией по эмитенту"""
    driver.get(SEARCH_URL)
    element = xpath_await_find(driver, SEARCH_FIELD)
    element.send_keys(ticker, Keys.ENTER)


def load_dividends_table(driver):
    """Выбирает на странице эмитента меню дивиденды и загружает таблицу с ними"""
    element = xpath_await_find(driver, DIVIDENDS_MENU)
    element.click()
    xpath_await_find(driver, DIVIDENDS_TABLE)


def get_html(ticker: str):
    """Возвращает html код страницы с данными по дивидендам и ее url"""
    driver_options = options.Options()
    driver_options.headless = True
    with webdriver.Firefox(options=driver_options) as driver:
        load_ticker_page(ticker, driver)
        load_dividends_table(driver)
        return driver.page_source, driver.current_url


def div_parser(data: str):
    if data == NO_VALUE:
        return 0.0
    data = re.search(DIV_PATTERN, data).group(0)
    data = data.replace(',', '.')
    return float(data)


def date_parser(data: str):
    if data == NO_VALUE:
        return None
    date = re.search(DATE_PATTERN, data).group(0)
    return pd.to_datetime(date, dayfirst=True)


class ConomyTableParser(AbstractTableParser):
    """Парсер таблиц с дивидендами с https://www.conomy.ru/"""
    TABLE_INDEX = TABLE_INDEX
    HEADER_TITLES = [[None, None, None, 'Дата закрытия реестра акционеров', None,
                      'Размер дивидендов\nна одну акцию, руб.'],
                     [None, None, None, None, 'Под выплату дивидендов', 'АОИ', 'АПИ']]
    FOOTER_TITLES = []
    DATA_COLUMNS = [DataColumn(DATE, 5, date_parser),
                    DataColumn(ORDINARY, 7, div_parser),
                    DataColumn(PREFERRED, 8, div_parser)]

    def __init__(self, ticker: str):
        self._ticker = ticker

    def get_html(self):
        return get_html(self._ticker)


if __name__ == '__main__':
    ticker_ = 'AKRN'
    table = ConomyTableParser(ticker_)
    print(table.df)
