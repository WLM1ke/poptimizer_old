"""ML-модель предсказания доходности"""
import pandas as pd
from hyperopt import hp

from ml import hyper
from ml.model_base import BaseModel
from ml.returns import cases

PARAMS = {'data': {'ew_lags': 7.370495526735477,
                   'returns_lags': 3},
          'model': {'bagging_temperature': 1.5669934364255877,
                    'depth': 1,
                    'ignored_features': (),
                    'l2_leaf_reg': 10.357858574063696,
                    'learning_rate': 0.06542676626215815,
                    'one_hot_max_size': 2,
                    'random_strength': 0.1029020796057046}}

# Диапазон лагов относительно базового, для которого осуществляется поиск оптимальной ML-модели
EW_LAGS_RANGE = 0.1
MAX_RETURNS_LAGS = 7


def ew_lags(base_params: dict, cut=1.0):
    lags = base_params['data']['ew_lags']
    return lags / (1 + cut * EW_LAGS_RANGE), lags * (1 + cut * EW_LAGS_RANGE)


def returns_lags():
    return [lag for lag in range(0, MAX_RETURNS_LAGS + 1)]


class ReturnsModel(BaseModel):
    """Содержит прогноз доходности и его СКО"""
    _PARAMS = PARAMS

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
        space = {'ew_lags': hp.uniform('ew_lags', *ew_lags(self._PARAMS)),
                 'returns_lags': hyper.make_choice_space('returns_lags', returns_lags())}
        return space

    def _check_data_space_bounds(self, params: dict):
        """Проверка, что параметры лежал не около границы вероятностного пространства"""
        lags = params['data']['ew_lags']
        lags_range = ew_lags(self._PARAMS, 0.9)
        if lags < lags_range[0] or lags_range[1] < lags:
            print(f'\nНеобходимо увеличить EW_LAGS_RANGE до {EW_LAGS_RANGE + 0.1:0.1f}')
        lag = params['data']['returns_lags']
        if lag == MAX_RETURNS_LAGS:
            print(f'\nНеобходимо увеличить MAX_RETURNS_LAGS до {MAX_RETURNS_LAGS + 1}')

    @property
    def prediction_mean(self):
        """pd.Series с прогнозом дивидендов"""
        data_pool = self._predict_pool_func(tickers=self.positions, last_date=self.date, **self._cv_result['data'])

        mean = pd.DataFrame(data_pool.get_features(), list(self.positions)).iloc[:, 2]
        std = pd.DataFrame(data_pool.get_features(), list(self.positions)).iloc[:, 1]

        return (pd.Series(self._clf.predict(data_pool), list(self.positions)) + mean) * std

    @property
    def prediction_std(self):
        """pd.Series с прогнозом дивидендов"""
        data_pool = self._predict_pool_func(tickers=self.positions, last_date=self.date, **self._cv_result['data'])
        return pd.DataFrame(data_pool.get_features(), list(self.positions)).iloc[:, 1] * self.std


if __name__ == '__main__':
    from trading import POSITIONS, DATE

    pred = ReturnsModel(tuple(sorted(POSITIONS)), pd.Timestamp(DATE))
    print(pred)
    pred.find_better_model()
