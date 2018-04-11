"""Организация хранения локальных DataFrames"""

import time
from pathlib import Path

import pandas as pd

from portfolio_optimizer import settings


def make_data_path(subfolder: str, file_name: str):
    """Создает подкаталог *subfolder* в директории данных и
       возвращает путь к файлу *file_name* в нем."""
    folder = settings.DATA_PATH / subfolder
    if not folder.exists():
        folder.mkdir(parents=True)
    return folder / file_name


class LocalFile:
    """Обеспечивает функционал сохранения, проверки наличия, загрузки и даты изменения для файла.

     Реализована поддержка для DataFrames и Series с корректным сохранением заголовков.
     """

    def __init__(self, subfolder: str, filename: str, converters: dict):
        """
        Инициирует объект.

        Parameters
        ----------
        subfolder
            Подкаталог, где хранятся данные.
        filename
            Наименование файла с данными.
        converters
            Словарь с конвертерами данных.
        """
        self.path = make_data_path(subfolder, filename)
        self.converters = converters

    def exists(self):
        """Проверка существования файла."""
        return self.path.exists()

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
        df = df.set_index(df.columns[0])
        if len(df.columns) == 1:
            return df[df.columns[0]]
        return df
