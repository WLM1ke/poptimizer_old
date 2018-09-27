"""Абстрактный класс ML-модели"""
import abc

import catboost
import pandas as pd

from ml import hyper


class DividendsML(abc.ABC):
    """Содержит прогноз и его СКО

    Parameters
    ----------
    positions
        Кортеж тикеров, для которых необходимо составить прогноз
    date
        Дата, для которой необходимо составить прогноз
    """
    # Словарь с параметрами ML-модели данных
    _PARAMS = None

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
                f'\n\nПрогноз:\n{self.prediction_mean}'
                f'\n\nВажность признаков: {self._clf.feature_importances_}'
                f'\n\nМодель:\n{self.params}')

    @staticmethod
    @abc.abstractmethod
    def _learn_pool_func(*args, **kwargs):
        """catboost.Pool с данными для обучения"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def _predict_pool_func(*args, **kwargs):
        """catboost.Pool с данными для предсказания"""
        raise NotImplementedError

    @abc.abstractmethod
    def _make_data_space(self):
        """Пространство поиска параметров данных модели"""
        raise NotImplementedError

    @abc.abstractmethod
    def _check_data_space_bounds(self, params: dict):
        """Проверка, что параметры лежал не около границы вероятностного пространства"""
        raise NotImplementedError

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
    @abc.abstractmethod
    def prediction_mean(self):
        """pd.Series с прогнозом дивидендов"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def prediction_std(self):
        """pd.Series с прогнозом дивидендов"""
        raise NotImplementedError

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
