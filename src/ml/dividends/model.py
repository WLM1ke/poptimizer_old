"""ML-модель для предсказания дивидендов"""
import catboost
import pandas as pd

from ml import hyper
from ml.dividends import cases
from utils.aggregation import Freq

PARAMS = {'data': {'freq': Freq.yearly,
                   'lags': 1},
          'model': {'bagging_temperature': 1.1542008340618164,
                    'depth': 4,
                    'l2_leaf_reg': 2.7558209934423616,
                    'learning_rate': 0.02991973118954086,
                    'one_hot_max_size': 100,
                    'random_strength': 1.024116898045557}}

# Диапазон лагов относительно базового, для которого осуществляется поиск оптимальной ML-модели
LAGS_RANGE = 1


def lags(base_params: dict):
    """Список лагов для оптимизации - должны быть больше 0"""
    base_lags = base_params['data']['lags']
    return [lag for lag in range(base_lags - LAGS_RANGE, base_lags + LAGS_RANGE + 1) if lag > 0]


class DividendsML:
    """Содержит прогноз дивидендов и его СКО

    Parameters
    ----------
    positions
        Кортеж тикеров, для которых необходимо составить прогноз
    date
        Дата, для которой необходимо составить прогноз
    """
    _PARAMS = PARAMS

    def __init__(self, positions: tuple, date: pd.Timestamp):
        self._positions = positions
        self._date = date
        self._cv_result = hyper.cv_model(self._PARAMS, positions, date, self._learn_pool_func)
        self._clf = catboost.CatBoostRegressor(**self._cv_result['model'])
        learn_data = self._learn_pool_func(tickers=positions, last_date=date, **self._cv_result['data'])
        self._clf.fit(learn_data)

    def __str__(self):
        return (f'СКО - {self.std:0.4%}'
                f'\nR2 - {self.r2:0.4%}'
                f'\n\nПрогноз:\n{self.prediction}'
                f'\n\nВажность признаков: {self._clf.feature_importances_}'
                f'\n\nМодель:\n{self.params}')

    @staticmethod
    def _learn_pool_func(*args, **kwargs):
        """catboost.Pool с данными для обучения"""
        return cases.learn_pool(*args, **kwargs)

    @staticmethod
    def _predict_pool_func(*args, **kwargs):
        """catboost.Pool с данными для предсказания"""
        return cases.predict_pool(*args, **kwargs)

    def _make_data_space(self):
        """Пространство поиска параметров данных модели"""
        space = {'freq': hyper.make_choice_space('freq', Freq),
                 'lags': hyper.make_choice_space('lags', lags(self._PARAMS))}
        return space

    def _check_data_space_bounds(self, params: dict):
        """Проверка, что параметры лежал не около границы вероятностного пространства"""
        lag = params['data']['lags']
        if lag != 1 and (lag == lags(self._PARAMS)[0] or lag == lags(self._PARAMS)[-1]):
            print(f'\nНеобходимо увеличить LAGS_RANGE до {LAGS_RANGE + 1}')

    @property
    def positions(self):
        """Перечень позиций, для которых составлен прогноз"""
        return self._positions

    @property
    def date(self):
        """Дата, для которой составлен прогноз"""
        return self._date

    @property
    def std(self):
        """СКО прогноза"""
        return self._cv_result['std']

    @property
    def r2(self):
        """СКО прогноза"""
        return self._cv_result['r2']

    @property
    def prediction(self):
        """pd.Series с прогнозом дивидендов"""
        pred_data = self._predict_pool_func(tickers=self.positions, last_date=self.date, **self._cv_result['data'])
        return pd.Series(self._clf.predict(pred_data), list(self.positions))

    @property
    def params(self):
        """Ключевые параметры модели"""
        return dict(data=self._cv_result['data'],
                    model=self._cv_result['model'])

    def find_better_model(self):
        """Ищет оптимальную модель и сравнивает с базовой - результаты сравнения распечатываются"""
        positions = self._positions
        date = self._date
        base_cv_results = hyper.cv_model(self._PARAMS, positions, date, self._learn_pool_func)
        find_params = hyper.optimize_hyper(self._PARAMS, positions, date,
                                           self._learn_pool_func, self._make_data_space())
        self._check_data_space_bounds(find_params)
        best_cv_results = hyper.cv_model(find_params, positions, date, self._learn_pool_func)
        if base_cv_results['loss'] < best_cv_results['loss']:
            print('\nЛУЧШАЯ МОДЕЛЬ - Базовая модель')
            print(f"R2 - {base_cv_results['r2']:0.4%}"
                  f"\nКоличество итераций - {base_cv_results['model']['iterations']}"
                  f"\n{self._PARAMS}")
            print('\nНайденная модель')
            print(f"R2 - {best_cv_results['r2']:0.4%}"
                  f"\nКоличество итераций - {best_cv_results['model']['iterations']}"
                  f"\n{find_params}")
        else:
            print('\nЛУЧШАЯ МОДЕЛЬ - Найденная модель')
            print(f"R2 - {best_cv_results['r2']:0.4%}"
                  f"\nКоличество итераций - {best_cv_results['model']['iterations']}"
                  f"\n{find_params}")
            print('\nБазовая модель')
            print(f"R2 - {base_cv_results['r2']:0.4%}"
                  f"\nКоличество итераций - {base_cv_results['model']['iterations']}"
                  f"\n{self._PARAMS}")


if __name__ == '__main__':
    from trading import POSITIONS, DATE
    pred = DividendsML(tuple(sorted(POSITIONS)), pd.Timestamp(DATE))
    print(pred)
    pred.find_better_model()

    # СКО - 3.9547%
