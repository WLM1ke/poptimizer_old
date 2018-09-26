"""Модель для предсказания дивидендов"""
import catboost
import pandas as pd

from ml import hyper
from ml.dividends import cases
from utils.aggregation import Freq

P_____ = {'data': {'freq': Freq.yearly,
                   'lags': 1},
          'model': {'bagging_temperature': 1.1309994272659563,
                    'depth': 5,
                    'l2_leaf_reg': 1.6947129385586475,
                    'learning_rate': 0.1229294573322397,
                    'one_hot_max_size': 100,
                    'random_strength': 2.6665434457041237}}

PARAMS = {'data': {'freq': Freq.yearly,
                   'lags': 1},
          'model': {'bagging_temperature': 0.8514582238067644,
                    'depth': 4,
                    'l2_leaf_reg': 3.100562393381714,
                    'learning_rate': 0.0883151996608085,
                    'one_hot_max_size': 100,
                    'random_strength': 0.992155907806343}}

# Количество лагов в данных
LAGS_RANGE = 1


def lags():
    base_lags = PARAMS['data']['lags']
    return [lag for lag in range(base_lags - LAGS_RANGE, base_lags + LAGS_RANGE + 1) if lag > 0]


def make_param_space():
    """Пространство поиска параметров модели"""
    space = {
        'data': {'freq': hyper.make_choice_space('freq', Freq),
                 'lags': hyper.make_choice_space('lags', lags())},
        'model': hyper.make_model_space(PARAMS)}
    return space


def check_space_bounds(params: dict):
    data = params['data']
    if data['lags'] != 1 and (data['lags'] == lags()[0] or data['lags'] == lags()[-1]):
        print(f'\nНеобходимо увеличить LAGS_RANGE до {LAGS_RANGE + 1}')
    hyper.check_model_bounds(params, PARAMS)


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
        self._cv_result = hyper.cv_model(PARAMS, positions, date, cases.learn_pool)
        self._clf = catboost.CatBoostRegressor(**self._cv_result['model'])
        learn_data = cases.learn_pool(tickers=positions, last_date=date, **self._cv_result['data'])
        self._clf.fit(learn_data)
        pred_data = cases.predict_pool(tickers=positions, last_date=date, **self._cv_result['data'])
        self._prediction = pd.Series(self.predict(pred_data), list(self._positions))

    def __str__(self):
        return (f'СКО - {self.std:0.4%}'
                f'\nR2 - {self.r2:0.4%}'
                f'\n\nПрогноз:\n{self.div_prediction}'
                f'\n\nВажность признаков: {self._clf.feature_importances_}'
                f'\n\nМодель:\n{self.params}')

    @property
    def positions(self):
        return self._positions

    @property
    def date(self):
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
    def div_prediction(self):
        """pd.Series с прогнозом дивидендов"""
        return self._prediction

    @property
    def params(self):
        """Ключевые параметры модели"""
        return dict(data=self._cv_result['data'],
                    model=self._cv_result['model'])

    def predict(self, pred_data):
        """Данные, по которым нужно построить прогноз - первая колонка с тикерами"""
        return self._clf.predict(pred_data)

    def find_better_model(self):
        """Ищет оптимальную модель и сравнивает с базовой - результаты сравнения распечатываются"""
        positions = self._positions
        date = self._date
        base = hyper.cv_model(PARAMS, positions, date, cases.learn_pool)
        param_space = make_param_space()
        best_model_params = hyper.optimize_hyper(param_space, positions, date, cases.learn_pool)
        check_space_bounds(best_model_params)
        best = hyper.cv_model(best_model_params, positions, date, cases.learn_pool)
        if base['loss'] < best['loss']:
            print('\nЛУЧШАЯ МОДЕЛЬ - Базовая модель')
            print(f"R2 - {base['r2']:0.4%}"
                  f"\nКоличество итераций - {base['model']['iterations']}"
                  f"\n{PARAMS}")
            print('\nНайденная модель')
            print(f"R2 - {best['r2']:0.4%}"
                  f"\nКоличество итераций - {best['model']['iterations']}"
                  f"\n{best_model_params}")
        else:
            print('\nЛУЧШАЯ МОДЕЛЬ - Найденная модель')
            print(f"R2 - {best['r2']:0.4%}"
                  f"\nКоличество итераций - {best['model']['iterations']}"
                  f"\n{best_model_params}")
            print('\nБазовая модель')
            print(f"R2 - {base['r2']:0.4%}"
                  f"\nКоличество итераций - {base['model']['iterations']}"
                  f"\n{PARAMS}")


if __name__ == '__main__':
    from trading import POSITIONS, DATE
    pred = DividendsML(tuple(sorted(POSITIONS)), pd.Timestamp(DATE))
    print(pred)
    pred.find_better_model()

    # СКО - 3.9547%
