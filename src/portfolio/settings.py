"""Global package settings."""

from pathlib import Path

# QUESTION: зачем нужно переименовывать строки в константы?
# Основные метки столбцов в фреймах данных
CLOSE_PRICE = 'CLOSE_PRICE'
CPI = 'CPI'
DATE = 'DATE'
DIVIDENDS = 'DIVIDENDS'
LAST_PRICE = 'LAST_PRICE'
LOT_SIZE = 'LOT_SIZE'
COMPANY_NAME = 'COMPANY_NAME'
REG_NUMBER = 'REG_NUMBER'
TICKER = 'TICKER'
TICKER_ALIASES = 'TICKER_ALIASES'
VOLUME = 'VOLUME'
# Путь к данным - данные состоящие из нескольких серий хранятся в отдельных директориях внутри базовой директории
DATA_PATH = Path(__file__).parents[2] / 'data'

# FIXME: file_name - лучше первый аргумент
def make_data_path(folder, file_name: str) -> Path:
    """Создает директорию в директории данных и возвращает путь к файлу в ней."""
    if folder is None:
        folder = DATA_PATH
    else:
        folder = DATA_PATH / folder
    if not folder.exists():
        folder.mkdir(parents=True)
    return folder / file_name
