"""Сохраняет, обновляет и загружает локальную версию данных"""

from local.local_cpi import cpi, cpi_to_date
from local.local_dividends import monthly_dividends
from local.local_dividends_dohod import dividends_dohod
from local.local_dividends_smart_lab import dividends_smart_lab
from local.local_index import index
from local.local_quotes import prices
from local.local_quotes import volumes
from local.local_securities_info import lot_size
