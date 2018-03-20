"""Global package settings."""

from pathlib import Path

# Основные метки столбцов в DataFrame
CPI = 'CPI'
DATE = 'DATE'
DIVIDENDS = 'DIVIDENDS'
# Путь к данным - данные состоящие из нескольких серий хранятся в директориях внутри базовой директории
DATA_PATH = Path(__file__).parents[2] / 'data'


def make_data_path(folder, file_name: str) -> Path:
    """Создает директорию в директории данных и возвращает путь к файлу в ней."""
    if folder is None:
        folder = DATA_PATH
    else:
        folder = DATA_PATH / folder
    if not folder.exists():
        folder.mkdir(parents=True)
    return folder / file_name
