"""Загрузка данных о дивидендах с https://www.conomy.ru/"""
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import wait

# webdriver.Safari
WEB_DRIVER = webdriver.Safari

# Параметры поиска страницы эмитента
SEARCH_URL = 'https://www.conomy.ru/search'
SEARCH_FIELD = "issuer_search"
WAITING_TIME = 10

# Параметры поиска данных по дивидендам
DIVIDENDS_MENU = '//*[@id="page-wrapper"]/div/nav/ul/li[5]/a'


def find_ticker_page(ticker: str, driver):
    driver.get(SEARCH_URL)
    title = driver.title
    element = driver.find_element_by_id(SEARCH_FIELD)
    element.send_keys(ticker, Keys.ENTER)
    wait.WebDriverWait(driver_, WAITING_TIME).until_not(expected_conditions.title_is(title))


def load_dividends_table(driver):
    element = driver.find_element_by_xpath(DIVIDENDS_MENU)
    element.click()


if __name__ == '__main__':
    ticker_ = 'CHMF'
    driver_ = WEB_DRIVER()
    find_ticker_page(ticker_, driver_)
    load_dividends_table(driver_)
