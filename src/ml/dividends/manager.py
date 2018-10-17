"""Менеджер данных с обученной ML-моделью дивидендов"""
import pandas as pd

from ml.dividends import model
from ml.manager_ml import MLDataManager

ML_NAME = 'dividends_ml'


class DividendsMLDataManager(MLDataManager):
    """Хранения данных по прогнозу дивидендов на основе ML

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
        super().__init__(positions, date, model.DividendsModel, ML_NAME)


if __name__ == '__main__':
    pos = tuple(sorted(['AKRN', 'BANEP', 'CHMF', 'GMKN', 'LKOH', 'LSNGP', 'LSRG', 'MSRS', 'MSTT', 'MTSS', 'PMSBP',
                        'RTKMP', 'SNGSP', 'TTLK', 'UPRO', 'VSMO',
                        'PRTK', 'MVID', 'IRKT', 'TATNP']))
    DATE = '2018-09-04'
    pred = DividendsMLDataManager(pos, pd.Timestamp(DATE)).value
    print(pred)
    pred.find_better_model()
