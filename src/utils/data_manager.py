"""Абстрактный класс менеджера создания, обновления и предоставления локальных данных"""

from abc import ABC, abstractmethod

import arrow
import numpy as np
import pandas as pd

from utils.data_file import DataFile

# Часовой пояс MOEX
MARKET_TIME_ZONE = 'Europe/Moscow'
# Торги заканчиваются в 19.00, но данные публикуются 19.45
END_OF_TRADING_DAY = dict(hour=19, minute=45, second=0, microsecond=0)


class AbstractDataManager(ABC):
    """Организация создания, обновления и предоставления локальных DataFrame"""

    # Требования к индексу данных
    is_unique = True
    is_monotonic = True
    # Нужно ли перезаписать новыми данными с нуля при обновлении
    update_from_scratch = False

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
        self._data = DataFile(data_category, data_name)
        if self._data.last_update is None:
            self.create()
        elif self.next_update < arrow.now():
            self.update()

    def __str__(self):
        return (f'Последнее обновление - {self.last_update}\n'
                f'Следующее обновление - {self.next_update}\n'
                f'\n'
                f'{self.value}')

    @property
    def data_category(self):
        """Категория данных"""
        return self._data.data_category

    @property
    def data_name(self):
        """Название данных"""
        return self._data.data_name

    @property
    def value(self):
        """Возвращает сохраненное значение данных. Если сохраненного значения нет, то None"""
        return self._data.value

    @property
    def last_update(self):
        """Время обновления данных - arrow в часовом поясе MOEX"""
        return arrow.get(self._data.last_update).to(MARKET_TIME_ZONE)

    @property
    def next_update(self):
        """Время следующего планового обновления данных - arrow в часовом поясе MOEX"""
        last_update = self.last_update
        end_of_trading_day = last_update.replace(**END_OF_TRADING_DAY)
        if last_update > end_of_trading_day:
            return end_of_trading_day.shift(days=1)
        return end_of_trading_day

    @abstractmethod
    def download_all(self):
        """Загружает все необходимые данные и при необходимости проводит их первичную обработку"""
        raise NotImplementedError

    @abstractmethod
    def download_update(self):
        """Загружает данные с последнего значения включительно в существующих данных

        При отсутствии возможности частичной загрузки должна сохраняться реализация из абстрактного класса, а данные
        будут загружены полностью
        """
        raise NotImplementedError

    def create(self):
        """Создает локальный файл с нуля или перезаписывает существующий

        Индекс данных проверяется на уникальность и монотонность
        """
        print(f'Создание локальных данных с нуля {self._data.data_category} -> {self._data.data_name}')
        df = self.download_all()
        self._validate_index(df)
        self._data.value = df

    def _validate_index(self, df):
        if self.is_unique and not df.index.is_unique:
            raise ValueError(f'У новых данных индекс не уникальный')
        if self.is_monotonic and not df.index.is_monotonic_increasing:
            raise ValueError(f'У новых данных индекс не возрастает монотонно')

    def update(self):
        """Обновляет локальные данные

        При наличии флага перезапись с нуля используется метод создания новых данных
        При отсутствии реализации функции частичной загрузки данных будет осуществлена их полная загрузка
        Во время обновления проверяется совпадение новых данных со существующими
        Индекс всех данных проверяется на уникальность и монотонность
        """
        if self.update_from_scratch:
            self.create()
            return
        print(f'Обновление локальных данных {self._data.data_category} -> {self._data.data_name}')
        df_old = self.value
        try:
            df_new = self.download_update()
        except NotImplementedError:
            df_new = self.download_all()
        self._validate_new(df_old, df_new)
        old_elements = df_old.index.difference(df_new.index)
        df = df_old.loc[old_elements].append(df_new)
        self._validate_index(df)
        self._data.value = df

    def _validate_new(self, df_old, df_new):
        """Проверяет соответствие новых данных существующим"""
        common_index = df_old.index.intersection(df_new.index)
        if isinstance(df_old, pd.Series):
            condition = np.allclose(df_old.loc[common_index], df_new.loc[common_index])
        else:
            condition_not_object = np.allclose(df_old.select_dtypes(exclude='object').loc[common_index],
                                               df_new.select_dtypes(exclude='object').loc[common_index],
                                               equal_nan=True)
            df_new_object = df_new.select_dtypes(include='object').loc[common_index]
            condition_object = df_old.select_dtypes(include='object').loc[common_index].equals(df_new_object)
            condition = condition_not_object and condition_object
        if not condition:
            raise ValueError(f'Ошибка обновления данных - существующие данные не соответствуют новым:\n'
                             f'Категория - {self._data.data_category}\n'
                             f'Название - {self._data.data_name}\n')
