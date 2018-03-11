"""Global package settings"""

from pathlib import Path

DATA_PATH = Path(__file__).parents[2] / 'data'


def make_data_path(folder: str, file_name: str) -> Path:
    """Создает поддиректорию в директории данных и возвращает путь к файлу в ней."""
    folder = DATA_PATH / folder
    if not folder.exists():
        folder.mkdir(parents=True)
    # FIXME: лучше выдавать путь str(folder / file_name)      
    return folder / file_name
