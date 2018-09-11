"""Хранение и обновление локальной версии данных по дивидендам"""
from local.dividends.dividends_status import smart_lab_status, dividends_status
from local.dividends.dohod_ru import dividends_dohod as dohod
from local.dividends.smart_lab_ru import dividends_smart_lab as smart_lab
from local.dividends.sqlite import monthly_dividends
from local.dividends.sqlite import tickers_dividends as dividends
