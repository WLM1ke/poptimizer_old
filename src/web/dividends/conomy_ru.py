"""Загрузка данных о дивидендах с https://www.conomy.ru/"""
import re

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox import options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import wait

from web.dividends import parser
from web.labels import DATE

# Время ожидания загрузки
WAITING_TIME = 10

# Параметры поиска страницы эмитента
SEARCH_URL = 'https://www.conomy.ru/search'
SEARCH_FIELD = '//*[@id="issuer_search"]'

# Параметры поиска данных по дивидендам
DIVIDENDS_MENU = '//*[@id="page-wrapper"]/div/nav/ul/li[5]/a'
DIVIDENDS_TABLE = '//*[@id="page-container"]/div[2]/div/div[1]'

# Параметры парсинга таблицы с дивидендами
TABLE_INDEX = 1
HEADER_SIZE = 2
NO_VALUE = '-'
DIV_PATTERN = r'.*\d'
DATE_PATTERN = r'\d{2}\.\d{2}\.\d{4}'


def date_parser(data: str):
    """Функция парсинга значений в колонке с датами закрытия реестра"""
    if data == NO_VALUE:
        return None
    date = re.search(DATE_PATTERN, data).group(0)
    return pd.to_datetime(date, dayfirst=True)


DATE_COLUMN = parser.DataColumn(5,
                                {0: 'Дата закрытия реестра акционеров',
                                 1: 'Под выплату дивидендов'},
                                date_parser)


def div_parser(data: str):
    """Функция парсинга значений в колонке с дивидендами"""
    if data == NO_VALUE:
        return 0.0
    data = re.search(DIV_PATTERN, data).group(0)
    data = data.replace(',', '.')
    return float(data)


COMMON_TICKER_LENGTH = 4
COMMON_COLUMN = parser.DataColumn(7,
                                  {0: 'Размер дивидендов\nна одну акцию, руб.',
                                   1: 'АОИ'},
                                  div_parser)
PREFERRED_TICKER_ENDING = 'P'
PREFERRED_COLUMN = parser.DataColumn(8,
                                     {0: 'Размер дивидендов\nна одну акцию, руб.',
                                      1: 'АПИ'},
                                     div_parser)


def xpath_await(driver, xpath: str, waiting_time: int = WAITING_TIME):
    """Ищет и возвращает элемент с заданным xpath

    При необходимости предварительно ждет загрузки в течении определенного количества секунд
    """
    waiting_driver = wait.WebDriverWait(driver, waiting_time)
    element_xpath = expected_conditions.presence_of_element_located((By.XPATH, xpath))
    element = waiting_driver.until(element_xpath)
    return element


def load_ticker_page(driver, ticker: str):
    """Вводит в поле поиска тикер и переходит на страницу с информацией по эмитенту"""
    driver.get(SEARCH_URL)
    element = xpath_await(driver, SEARCH_FIELD)
    element.send_keys(ticker, Keys.ENTER)


def load_dividends_table(driver):
    """Выбирает на странице эмитента меню дивиденды и дожидается загрузки таблиц с ними"""
    element = xpath_await(driver, DIVIDENDS_MENU)
    element.click()
    xpath_await(driver, DIVIDENDS_TABLE)


def get_html(ticker: str):
    """Возвращает html-код страницы с данными по дивидендам с сайта https://www.conomy.ru/"""
    driver_options = options.Options()
    driver_options.headless = True
    with webdriver.Firefox(options=driver_options) as driver:
        load_ticker_page(driver, ticker)
        load_dividends_table(driver)
        return driver.page_source


def is_common(ticker: str):
    """Определяет является ли акция обыкновенной"""
    if len(ticker) == COMMON_TICKER_LENGTH:
        return True
    elif len(ticker) == COMMON_TICKER_LENGTH + 1 and ticker[COMMON_TICKER_LENGTH] == PREFERRED_TICKER_ENDING:
        return False
    raise ValueError(f'Некорректный тикер {ticker}')


def dividends_conomy(ticker: str):
    """Возвращает Series с дивидендами упорядоченными по возрастанию даты закрытия реестра

    Parameters
    ----------
    ticker
        Тикер

    Returns
    -------
    pandas.Series
        Строки - даты закрытия реестра упорядоченные по возрастанию
        Значения - дивиденды
    """
    html = get_html(ticker)
    table = parser.HTMLTableParser(html, TABLE_INDEX)
    columns = [DATE_COLUMN]
    if is_common(ticker):
        columns.append(COMMON_COLUMN)
    else:
        columns.append(PREFERRED_COLUMN)
    df = table.make_df(columns, HEADER_SIZE)
    df.dropna(inplace=True)
    df.columns = [DATE, ticker]
    df.set_index(DATE, inplace=True)
    df.sort_index(inplace=True)
    return df[ticker]


if __name__ == '__main__':
    print(dividends_conomy('NKHP'))
