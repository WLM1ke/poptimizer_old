"""Global package settings."""

from pathlib import Path

# Основные метки столбцов в фреймах данных
CASH = 'CASH'
CLOSE_PRICE = 'CLOSE_PRICE'
CPI = 'CPI'
DATE = 'DATE'
DIVIDENDS = 'DIVIDENDS'
LAST_PRICE = 'LAST_PRICE'
LAST_VALUE = 'LAST_VALUE'
LAST_WEIGHT = 'LAST_WEIGHT'
LOTS = 'LOTS'
LOT_SIZE = 'LOT_SIZE'
COMPANY_NAME = 'COMPANY_NAME'
PRICE = 'PRICE'
PORTFOLIO = 'PORTFOLIO'
REG_NUMBER = 'REG_NUMBER'
TICKER = 'TICKER'
TICKER_ALIASES = 'TICKER_ALIASES'
VOLUME = 'VOLUME'
VALUE = 'VALUE'
WEIGHT = 'WEIGHT'

# Путь к данным - данные состоящие из нескольких серий хранятся в отдельных директориях внутри базовой директории
DATA_PATH = Path(__file__).parents[2] / 'data'


def make_data_path(subfolder, file_name: str):
    """Создает директорию в директории данных и возвращает путь к файлу в ней."""
    folder = DATA_PATH / subfolder
    if not folder.exists():
        folder.mkdir(parents=True)
    return folder / file_name
