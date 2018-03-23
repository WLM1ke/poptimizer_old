"""Global package settings."""

from pathlib import Path

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
# QUESTION: Не очень пойму почему - мне как-то естественно, что сначала идет название каталога, а потом название файла.

# EP: коде используется как make_data_path(None, 'file.csv')
#     выглядит очень странно, совершенно не проходит под "наименьшее удивление"
#     и портит читаемость

#     предлагается:
#     make_data_path_root(file_name: str)
#     make_data_path_subfolder(file_name: str, subfolder: str)
#     или (чуть хуже)
#     make_data_path(file_name: str, subfolder = None)

# Резюме:  как сейчас оставлять для читаемости нежелательно

# QUESTION: А вариант хранить данные всегда в подкаталогах, убрать поддержку None для этого аргумента в функции и
#           оставить порядок аргументов, как есть?


def make_data_path(folder, file_name: str) -> Path:
    """Создает директорию в директории данных и возвращает путь к файлу в ней."""
    if folder is None:
        folder = DATA_PATH
    else:
        folder = DATA_PATH / folder
    if not folder.exists():
        folder.mkdir(parents=True)
    return folder / file_name
