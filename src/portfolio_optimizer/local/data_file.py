"""Организация хранения локальных DataFrames"""

import json

import arrow
import pandas as pd

from portfolio_optimizer import settings

INDEX_FILE_NAME = 'index.json'
DATA_FILE_EXTENSION = '.msg'


class DataFile:
    """Обеспечивает функционал сохранения, загрузки и даты изменения для файла

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
    def _make_data_path(subfolder, file: str):
        """Возвращает путь к файлу и при необходимости создает необходимые директории

        Директории создаются в глобальной директории данных из файла настроек
        """
        if subfolder is None:
            folder = settings.DATA_PATH
        else:
            folder = settings.DATA_PATH / subfolder
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
                return arrow.get(date)
            return date
        return None

    def dump(self, df):
        """Сохраняет DataFrame и обновляет информацию в индексе"""
        df.to_msgpack(self.data_path)
        if self.index_path.exists():
            with self.index_path.open('r') as file:
                index_dict = json.load(file)
        else:
            index_dict = {}
        index_dict[f'{self.frame_category}->{self.frame_name}'] = arrow.now().for_json()
        with self.index_path.open('w') as file:
            json.dump(index_dict, file, sort_keys=True, indent=2)

    def load(self):
        """Загружает данные из файла"""
        if self.last_update() is not None:
            return pd.read_msgpack(self.data_path)
