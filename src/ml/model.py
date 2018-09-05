"""Модель для предсказания дивидендов"""
import catboost
import pandas as pd

from ml import hyper, cases
from ml.cases import Freq

PARAMS = {'data': {'freq': Freq.yearly,
                   'lags': 1},
          'model': {'bagging_temperature': 1.3543429685644746,
                    'depth': 3,
                    'l2_leaf_reg': 2.4824258326685467,
                    'learning_rate': 0.0992972754295861,
                    'one_hot_max_size': 2,
                    'random_strength': 1.1362349258520674}}


class DividendsML:
    """Содержит прогноз дивидендов и его СКО

    Parameters
    ----------
    positions
        Кортеж тикеров, для которых необходимо составить прогноз
    date
        Дата, для которой необходимо составить прогноз
    """

    def __init__(self, positions: tuple, date: pd.Timestamp):
        self._positions = positions
        self._date = date
        self._cv_result = hyper.cv_model(PARAMS, positions, date)
        clf = catboost.CatBoostRegressor(**self._cv_result['model'])
        learn_data = cases.learn_pool(tickers=positions, last_date=date, **self._cv_result['data'])
        clf.fit(learn_data)
        pred_data = cases.predict_pool(tickers=positions, last_date=date, **self._cv_result['data'])
        self._prediction = pd.Series(clf.predict(pred_data), list(positions))

    def __str__(self):
        return (f'СКО - {self.std:0.4%}'
                f'\n\nПрогноз:\n{self.div_prediction}'
                f'\n\nМодель:\n{self.model_params}')

    @property
    def positions(self):
        return self._positions

    @property
    def date(self):
        return self._date

    @property
    def std(self):
        """СКО прогноза"""
        return self._cv_result['loss']

    @property
    def div_prediction(self):
        """pd.Series с прогнозом дивидендов"""
        return self._prediction

    @property
    def model_params(self):
        """Ключевые параметры модели"""
        return dict(data=self._cv_result['data'],
                    model=self._cv_result['model'])

    def find_better_model(self):
        """Ищет оптимальную модель и сравнивает с базовой - результаты сравнения распечатываются"""
        positions = self._positions
        date = self._date
        base = hyper.cv_model(PARAMS, positions, date)
        best_model_params = hyper.optimize_hyper(positions, date)
        best = hyper.cv_model(best_model_params, positions, date)
        if base['loss'] < best['loss']:
            print('\nЛУЧШАЯ МОДЕЛЬ - Базовая модель')
            print(f"СКО - {base['loss']:0.4%}"
                  f"\nКоличество итераций - {base['model']['iterations']}"
                  f"\n{PARAMS}")
            print('\nНайденная модель')
            print(f"СКО - {best['loss']:0.4%}"
                  f"\nКоличество итераций - {best['model']['iterations']}"
                  f"\n{best_model_params}")
        else:
            print('\nЛУЧШАЯ МОДЕЛЬ - Найденная модель')
            print(f"СКО - {best['loss']:0.4%}"
                  f"\nКоличество итераций - {best['model']['iterations']}"
                  f"\n{best_model_params}")
            print('\nБазовая модель')
            print(f"СКО - {base['loss']:0.4%}"
                  f"\nКоличество итераций - {base['model']['iterations']}"
                  f"\n{PARAMS}")


if __name__ == '__main__':
    pos = tuple(sorted(['AKRN', 'BANEP', 'CHMF', 'GMKN', 'LKOH', 'LSNGP', 'LSRG', 'MSRS', 'MSTT', 'MTSS', 'PMSBP',
                        'RTKMP', 'SNGSP', 'TTLK', 'UPRO', 'VSMO',
                        'PRTK', 'MVID', 'IRKT', 'TATNP']))
    DATE = '2018-09-04'
    pred = DividendsML(pos, pd.Timestamp(DATE))
    print(pred)
    pred.find_better_model()

    # СКО - 4.3773%
