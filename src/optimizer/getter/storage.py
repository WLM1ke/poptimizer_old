"""Local file storage for pandas DataFrames."""

import time
from collections import OrderedDict
from pathlib import Path

import pandas as pd

from optimizer import settings


def make_data_path(subfolder: str, file_name: str):
    """Создает директорию в директории данных и возвращает путь к файлу в ней."""
    folder = settings.DATA_PATH / subfolder
    if not folder.exists():
        folder.mkdir(parents=True)
    return folder / file_name


class LocalFile:
    """Обеспечивает функционал сохранения, проверки наличия, загрузки и даты изменения для файла.

     Реализована поддержка для DataFrames и Series с корректным сохранением заголовков.
     """

    def __init__(self, subfolder: str, filename: str, converters: OrderedDict):
        self.path = make_data_path(subfolder, filename)
        self.converters = converters
        self._data_columns = [k for i, k in enumerate(converters) if i != 0]
        # Если колонок с данными 1, то надо выдавать Series при загрузке
        if len(self._data_columns) == 1:
            self._data_columns = self._data_columns[0]

    def exists(self):
        """Проверка существования файла."""
        if self.path.exists():
            return True
        return False

    def updated_days_ago(self):
        """Количество дней с последнего обновления файла.

        https://docs.python.org/3/library/os.html#os.stat_result.st_mtime
        """
        time_updated = Path(self.path).stat().st_mtime
        lag_sec = time.time() - time_updated
        return lag_sec / (60 * 60 * 24)

    def save(self, df):
        """Сохраняет DataFrame или Series с заголовками."""
        df.to_csv(self.path, index=True, header=True)

    def read(self):
        """Загружает данные из файла.

        Значение sep обеспечивает корректную загрузку с лидирующими пробелами, вставленными PyCharm.
        """
        df = pd.read_csv(self.path,
                         converters=self.converters,
                         header=0,
                         engine='python',
                         sep='\s*,')
        df = df.set_index('DATE')
        return df[self._data_columns]
