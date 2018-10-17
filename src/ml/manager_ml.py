"""Менеджер данных с обученной ML-моделью"""
import arrow
import pandas as pd

from utils.data_manager import AbstractDataManager


class MLDataManager(AbstractDataManager):
    """Хранения данных по прогнозу на основе ML-модели

    Данные обновляются по обычному расписанию AbstractDataManager + при изменение набора тикеров, даты или значений
    параметров ML-модели

    Parameters
    ----------
    positions
        Кортеж тикеров, для которых необходимо составить прогноз
    date
        Дата, для которой необходимо составить прогноз
    model_class
        Класс ML-модели
    file_name
        Наименование файла (без расширения) для хранения модели
    """
    is_unique = False
    is_monotonic = False
    update_from_scratch = True

    def __init__(self, positions: tuple, date: pd.Timestamp, model_class, file_name: str):
        self._positions = positions
        self._date = date
        self._model_class = model_class
        super().__init__(None, file_name)

    def download_all(self):
        return self._model_class(self._positions, self._date)

    def download_update(self):
        super().download_update()

    @property
    def next_update(self):
        """Время следующего планового обновления данных - arrow в часовом поясе MOEX"""
        if self._positions != self.value.positions or self._date != self.value.date:
            return arrow.now().shift(days=-1)
        model_params = self._model_class.PARAMS
        for outer_key in model_params:
            for inner_key in model_params[outer_key]:
                if model_params[outer_key][inner_key] != self.value.params[outer_key][inner_key]:
                    return arrow.now().shift(days=-1)
        return super().next_update
