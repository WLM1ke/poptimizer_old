"""Абстрактный класс ML-модели"""
from abc import ABC, abstractmethod

import catboost
import numpy as np
import pandas as pd

from ml import hyper


class AbstractModel(ABC):
    """Содержит прогноз и его СКО

    Parameters
    ----------
    positions
        Кортеж тикеров, для которых необходимо составить прогноз
    date
        Дата, для которой необходимо составить прогноз
    """
    # Словарь с параметрами ML-модели данных
    PARAMS = None

    def __init__(self, positions: tuple, date: pd.Timestamp):
        self._positions = positions
        self._date = date
        self._cv_result = hyper.cv_model(self.PARAMS, positions, date, self._learn_pool_func)
        clf = catboost.CatBoostRegressor(**self._cv_result['model'])
        learn_data = self._learn_pool_func(tickers=positions, last_date=date, **self._cv_result['data'])
        clf.fit(learn_data)
        self._feature_importances = pd.Series(clf.feature_importances_, learn_data.get_feature_names())
        predict_data = self._predict_pool_func(tickers=positions, last_date=date, **self._cv_result['data'])
        self._prediction = pd.Series(clf.predict(predict_data), list(self.positions))
        self._prediction_data = pd.DataFrame(predict_data.get_features(),
                                             index=list(self.positions),
                                             columns=predict_data.get_feature_names())

    def __str__(self):
        prediction = pd.concat([self.prediction_mean, self.prediction_std], axis=1)
        prediction.columns = ['mean', 'std']
        return (f'СКО - {self.std:0.4%}'
                f'\nR2 - {self.r2:0.4%}'
                f'\n\nПрогноз:\n{prediction}'
                f'\n\nВажность признаков:\n{self._feature_importances}'
                f'\n\nМодель:\n{self.params}')

    @staticmethod
    @abstractmethod
    def _learn_pool_params(*args, **kwargs):
        """Параметры для создания catboost.Pool для обучения"""
        raise NotImplementedError

    @property
    def _learn_pool_func(self):
        """catboost.Pool с данными для обучения"""
        return lambda *args, **kwargs: catboost.Pool(**self._learn_pool_params(*args, **kwargs))

    @staticmethod
    @abstractmethod
    def _predict_pool_func(*args, **kwargs):
        """catboost.Pool с данными для предсказания"""
        raise NotImplementedError

    @abstractmethod
    def _make_data_space(self):
        """Пространство поиска параметров данных модели"""
        raise NotImplementedError

    @abstractmethod
    def _check_data_space_bounds(self, params: dict):
        """Проверка, что параметры лежал не около границы вероятностного пространства"""
        raise NotImplementedError

    @property
    @abstractmethod
    def prediction_mean(self):
        """pd.Series с прогнозом дивидендов"""
        raise NotImplementedError

    @property
    @abstractmethod
    def prediction_std(self):
        """pd.Series с прогнозом дивидендов"""
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
    def params(self):
        """Ключевые параметры модели с количеством итераций"""
        return dict(data=self._cv_result['data'],
                    model=self._cv_result['model'])

    def find_better_model(self):
        """Ищет оптимальную модель и сравнивает с базовой - результаты сравнения распечатываются"""
        positions = self._positions
        date = self._date
        base_cv_results = self._cv_result
        find_params = hyper.optimize_hyper(self.PARAMS, positions, date,
                                           self._learn_pool_func, self._make_data_space())
        self._check_data_space_bounds(find_params)
        best_cv_results = hyper.cv_model(find_params, positions, date, self._learn_pool_func)
        if base_cv_results['loss'] < best_cv_results['loss']:
            print('\nЛУЧШАЯ МОДЕЛЬ - Базовая модель')
            print(f"R2 - {base_cv_results['r2']:0.4%}"
                  f"\nКоличество итераций - {base_cv_results['model']['iterations']}"
                  f"\n{self.PARAMS}")
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
                  f"\n{self.PARAMS}")

    def learning_curve(self, fractions=np.linspace(0.1, 1.0, 10)):
        """Рисует кривую обучения для заданных долей от общего количества данных"""
        hyper.learning_curve(self.params, self.positions, self.date, self._learn_pool_params, fractions)
