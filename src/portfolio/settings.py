"""Global package settings"""

from pathlib import Path

DATA_PATH = Path(__file__).parent / 'data'


def make_data_path(folder: str, file_name: str) -> Path:
    """Создает поддиректорию в директории данных и возвращает путь к файлу к ней."""
    folder = settings.DATA_PATH / folder
    if not folder.exists():
        folder.mkdir(parents=True)
    return folder / file_name
