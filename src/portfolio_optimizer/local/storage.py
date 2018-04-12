"""Организация хранения локальных DataFrames"""

import json

import arrow
import pandas as pd

from portfolio_optimizer import settings

INDEX_FILE_NAME = 'index.json'
DATA_FILE_EXTENSION = '.msg'
TIME_STAMP_FORMAT = 'YYYY-MM-DD HH:mm:ss ZZ'


class LocalFile:
    """Обеспечивает функционал сохранения, проверки наличия, загрузки и даты изменения для файла

    Данные хранятся в каталоге установленном в глобальных настройках. Каждая категория данных в отдельной подкаталоге.
    Каждый ряд в отдельном файле в формате MessagePack

    В корне каталога данных ведется файл index.json в виде словаря str(frame_category->frame_name): дата изменения
    """

    def __init__(self, frame_category: str, frame_name: str):
        self.frame_category = frame_category
        self.frame_name = frame_name
        self.data_path = self._make_data_path(frame_category, f'{frame_name}{DATA_FILE_EXTENSION}')
        self.index_path = self._make_data_path(None, INDEX_FILE_NAME)

    @staticmethod
    def _make_data_path(folder: str, file: str):
        """Возвращает путь к файлу и при необходимости создает необходимые директории

        Директории создаются в глобальной директории данных из файла настроек
        """
        if folder is None:
            folder = settings.DATA_PATH
        else:
            folder = settings.DATA_PATH / folder
        if not folder.exists():
            folder.mkdir(parents=True)
        return folder / file

    def last_update(self):
        """Возвращает дату последнего обновления из индекса

        Если данные отсутствуют в индексе, то возвращает None
        """
        if self.index_path.exists():
            with self.index_path.open('r') as file:
                update_dict = json.load(file)
            date = update_dict.get(f'{self.frame_category}->{self.frame_name}', None)
            if date:
                return arrow.get(date, TIME_STAMP_FORMAT)
            return date
        return None

    def dump(self, df):
        """Сохраняет DataFrame и обновляет информацию в индексе"""
        df.to_msgpack(self.data_path)
        if self.index_path.exists():
            with self.index_path.open('r') as file:
                update_dict = json.load(file)
        else:
            update_dict = {}
        update_dict[f'{self.frame_category}->{self.frame_name}'] = arrow.now().format(TIME_STAMP_FORMAT)
        with self.index_path.open('w') as file:
            json.dump(update_dict, file)

    def load(self):
        """Загружает данные из файла"""
        return pd.read_msgpack(self.data_path)
