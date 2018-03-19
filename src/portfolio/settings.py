"""Global package settings."""

from enum import Enum, unique
from pathlib import Path

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


@unique
class Labels(Enum):
    """Основные метки столбцов и строк в DataFrame."""
    cpi = 'CPI'
    date = 'DATE'
