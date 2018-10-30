"""Загрузка данных о дивидендах с https://www.conomy.ru/"""
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox import options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import wait

# Время ожидания загрузки
WAITING_TIME = 10

# Параметры поиска страницы эмитента
SEARCH_URL = 'https://www.conomy.ru/search'
SEARCH_FIELD = '//*[@id="issuer_search"]'

# Параметры поиска данных по дивидендам
DIVIDENDS_MENU = '//*[@id="page-wrapper"]/div/nav/ul/li[5]/a'
DIVIDENDS_TABLE = '//*[@id="page-container"]/div[2]/div/div[1]'


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


def get_html(ticker: str):
    """Возвращает html код страницы с данными по дивидендам"""
    driver_options = options.Options()
    driver_options.headless = True
    with webdriver.Firefox(options=driver_options) as driver:
        load_ticker_page(ticker, driver)
        load_dividends_table(driver)
        xpath_await_find(driver, DIVIDENDS_TABLE)
        return driver.page_source


if __name__ == '__main__':
    ticker_ = 'AKRN'
    html = get_html(ticker_)
    soup = BeautifulSoup(html, 'lxml')
    for table in soup.find_all('table'):
        print('*' * 50)
        print(table)
