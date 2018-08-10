"""Хранение локальных данных"""

import pickle

import settings
from local.data import Data

PICKLE_VERSION = pickle.HIGHEST_PROTOCOL
DATA_FILE_EXTENSION = f'.pickle{PICKLE_VERSION}'


class DataFile:
    """Обеспечивает функционал сохранения и загрузки объектов Data

    Данные хранятся в каталоге установленном в глобальных настройках
    Каждая категория данных в отдельной подкаталоге
    Каждый ряд в отдельном файле в формате Pickle
    """

    def __init__(self, data_category, data_name: str):
        """
        Parameters
        ----------
        data_category
            Каталог в котором хранятся однородные данные - может быть None, тогда данные будут сохраняться в корне
            глобального каталога данных
        data_name
            Название серии данных
        """
        self._data_category = data_category
        self._data_name = data_name
        if self.data_path.exists():
            with open(self.data_path, 'rb') as data_file:
                self._data = pickle.load(data_file)
        else:
            self._data = Data()

    def __str__(self):
        return (f'{self.__class__.__name__}('
                f'data_category={self.data_category}, '
                f'data_name={self.data_name}, '
                f'data={self._data})')

    @property
    def data_category(self):
        """Категория данных"""
        return self._data_category

    @property
    def data_name(self):
        """Название данных"""
        return self._data_name

    @property
    def data_path(self):
        """Возвращает путь к файлу и при необходимости создает необходимые директории

        Директории создаются в глобальной директории данных из файла настроек
        """
        folder = settings.DATA_PATH
        if self._data_category is not None:
            folder = folder / self._data_category
        if not folder.exists():
            folder.mkdir(parents=True)
        return folder / f'{self._data_name}{DATA_FILE_EXTENSION}'

    @property
    def value(self):
        """Возвращает сохраненное значение данных. Если сохраненного значения нет, то None"""
        return self._data.value

    @value.setter
    def value(self, value):
        """Сохраняет новое значение данных"""
        self._data.value = value
        with open(self.data_path, 'wb') as data_file:
            pickle.dump(self._data, data_file, protocol=PICKLE_VERSION)

    @property
    def last_update(self):
        """Время обновления данных - epoch. Если сохраненного значения нет, то None"""
        return self._data.last_update


if __name__ == '__main__':
    print(DataFile('qqq', 'qqq'))
