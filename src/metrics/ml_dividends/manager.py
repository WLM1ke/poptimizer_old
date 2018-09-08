"""Менеджер данных с обученной ML-моделью дивидендов"""
import pandas as pd

from metrics.ml_dividends import model
from utils.data_manager import AbstractDataManager

ML_NAME = 'dividends_ml'


class DividendsMLDataManager(AbstractDataManager):
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
    is_unique = False
    is_monotonic = False
    update_from_scratch = True

    def __init__(self, positions: tuple, date: pd.Timestamp):
        self._positions = positions
        self._date = date
        super().__init__(None, ML_NAME)
        if positions != self.value.positions or date != self.value.date:
            self.create()
            return
        for outer_key in model.PARAMS:
            for inner_key in model.PARAMS[outer_key]:
                if model.PARAMS[outer_key][inner_key] != self.value.params[outer_key][inner_key]:
                    self.create()
                    return

    def download_all(self):
        return model.DividendsML(self._positions, self._date)

    def download_update(self):
        super().download_update()


if __name__ == '__main__':
    pos = tuple(sorted(['AKRN', 'BANEP', 'CHMF', 'GMKN', 'LKOH', 'LSNGP', 'LSRG', 'MSRS', 'MSTT', 'MTSS', 'PMSBP',
                        'RTKMP', 'SNGSP', 'TTLK', 'UPRO', 'VSMO',
                        'PRTK', 'MVID', 'IRKT', 'TATNP']))
    DATE = '2018-09-04'
    pred = DividendsMLDataManager(pos, pd.Timestamp(DATE)).value
    print(pred)
    pred.find_better_model()
