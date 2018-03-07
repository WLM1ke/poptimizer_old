"""Dividends history downloader and parser."""

import bs4
import requests

# Посмотреть - http://html.python-requests.org
# При необходимости поменять requirements


url = 'https://www.dohod.ru/ik/analytics/dividend/rtkmp'
page = requests.get(url).content
soup = bs4.BeautifulSoup(page, "html5lib")
soup.find_all('table')
i = soup.find(name='p', attrs='table-title', string='Все выплаты').next_sibling
print(i)
