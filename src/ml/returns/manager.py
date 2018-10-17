"""Менеджер данных с обученной ML-моделью доходности"""
import pandas as pd

from ml.manager_ml import MLDataManager
from ml.returns import model

ML_NAME = 'returns_ml'


class ReturnsMLDataManager(MLDataManager):
    """Хранения данных по прогнозу доходности на основе ML-модели

    Данные обновляются по обычному расписанию AbstractDataManager + при изменение набора тикеров, даты или значений
    параметров ML-модели

    Parameters
    ----------
    positions
        Кортеж тикеров, для которых необходимо составить прогноз
    date
        Дата, для которой необходимо составить прогноз
    """
    def __init__(self, positions: tuple, date: pd.Timestamp):
        super().__init__(positions, date, model.ReturnsModel, ML_NAME)


if __name__ == '__main__':
    from trading import POSITIONS, DATE

    pred = ReturnsMLDataManager(tuple(sorted(POSITIONS)), pd.Timestamp(DATE)).value
    print(pred)
