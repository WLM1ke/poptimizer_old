"""Оптимизация гиперпараметров ML-модели дивидендов"""
import functools

import catboost
import hyperopt
import numpy as np
import pandas as pd
from hyperopt import hp

from metrics.ml_dividends.cases import learn_pool
from utils.aggregation import Freq

# Базовые настройки catboost
MAX_ITERATIONS = 600
SEED = 284704
FOLDS_COUNT = 20
BASE_PARAMS = dict(iterations=MAX_ITERATIONS,
                   random_state=SEED,
                   od_type='Iter',
                   verbose=False,
                   allow_writing_files=False)

# Настройки hyperopt
MAX_SEARCHES = 100

# Количество лагов в данных
MAX_LAG = 3

# Рекомендации Яндекс - https://tech.yandex.com/catboost/doc/dg/concepts/parameter-tuning-docpage/

# OneHot кодировка - учитывая количество акций в портфеле используется cat-кодировка или OneHot-кодировка
ONE_HOT_SIZE = [2, 100]

# Скорость обучения
MEAN_LEARNING_RATE = 0.1
RANGE_LEARNING_RATE = 0.2

# Глубина деревьев
MAX_DEPTH = 8

# L2-регуляризация
MEAN_L2 = 2.0
RANGE_L2 = 0.4

# Случайность разбиений
MEAN_RAND_STRENGTH = 1.3
RANGE_RAND_STRENGTH = 0.3

# Интенсивность бегинга
MEAN_BAGGING = 1.4
RANGE_BAGGING = 0.4


def log_limits(mean_, percent_range):
    """Логарифмический интервал"""
    log_x = np.log(mean_)
    log_delta = np.log1p(percent_range)
    return log_x - log_delta, log_x + log_delta


def make_log_space(space_name, mean_, percent_range):
    """Создает логарифмическое вероятностное пространство"""
    min_, max_ = log_limits(mean_, percent_range)
    return hp.loguniform(space_name, min_, max_)


def make_choice_space(space_name, choice):
    """Создает вероятностное пространство для выбора из нескольких вариантов

    Работает напрямую для iterable, а для int формирует выбор из range(1, choice + 1)
    """
    if isinstance(choice, int):
        choice = range(1, choice + 1)
    return hp.choice(space_name, list(choice))


# Описание пространства поиска параметров
PARAM_SPACE = {
    'data': {'freq': make_choice_space('freq', Freq),
             'lags': make_choice_space('lags', MAX_LAG)},
    'model': {'one_hot_max_size': make_choice_space('one_hot_max_size', ONE_HOT_SIZE),
              'learning_rate': make_log_space('learning_rate', MEAN_LEARNING_RATE, RANGE_LEARNING_RATE),
              'depth': make_choice_space('depth', MAX_DEPTH),
              'l2_leaf_reg': make_log_space('l2_leaf_reg', MEAN_L2, RANGE_L2),
              'random_strength': make_log_space('rand_strength', MEAN_RAND_STRENGTH, RANGE_RAND_STRENGTH),
              'bagging_temperature': make_log_space('bagging_temperature', MEAN_BAGGING, RANGE_BAGGING)}}


def check_space_bounds(space: dict):
    """Проверяет и дает рекомендации о расширении границ пространства поиска параметров

    Для целочисленных параметров - предупреждение выдается на границе диапазона и рекомендуется увеличить диапазон на 1.
    Для реальных параметров - предупреждение выдается в 10% от границе. Рекомендуется сместить центр поиска к текущему
    значению и расширить границы поиска на 10%
    """
    if space['data']['lags'] == MAX_LAG:
        print(f'\nНеобходимо увеличить MAX_LAG до {MAX_LAG + 1}')

    if abs(np.log(space['model']['learning_rate'] / MEAN_LEARNING_RATE)) / np.log1p(RANGE_LEARNING_RATE) > 0.9:
        new_mean = (MEAN_LEARNING_RATE + space['model']['learning_rate']) / 2
        print(f"\nНеобходимо изменить MEAN_LEARNING_RATE на {new_mean:0.2f}")
        print(f'Необходимо увеличить RANGE_LEARNING_RATE до {RANGE_LEARNING_RATE + 0.1:0.1f}')

    if space['model']['depth'] == MAX_DEPTH:
        print(f'\nНеобходимо увеличить MAX_DEPTH до {MAX_DEPTH + 1}')

    if abs(np.log(space['model']['l2_leaf_reg'] / MEAN_L2)) / np.log1p(RANGE_L2) > 0.9:
        new_mean = (MEAN_L2 + space['model']['l2_leaf_reg']) / 2
        print(f"\nНеобходимо изменить MEAN_L2 на {new_mean:0.1f}")
        print(f'Необходимо увеличить RANGE_L2 до {RANGE_L2 + 0.1:0.1f}')

    if abs(np.log(space['model']['random_strength'] / MEAN_RAND_STRENGTH)) / np.log1p(RANGE_RAND_STRENGTH) > 0.9:
        new_mean = (MEAN_RAND_STRENGTH + space['model']['random_strength']) / 2
        print(f"\nНеобходимо изменить MEAN_RAND_STRENGTH на {new_mean:0.1f}")
        print(f'Необходимо увеличить RANGE_RAND_STRENGTH до {RANGE_RAND_STRENGTH + 0.1:0.1f}')

    if abs(np.log(space['model']['bagging_temperature'] / MEAN_BAGGING)) / np.log1p(RANGE_BAGGING) > 0.9:
        new_mean = (MEAN_BAGGING + space['model']['bagging_temperature']) / 2
        print(f"\nНеобходимо изменить MEAN_BAGGING на {new_mean:0.1f}")
        print(f'Необходимо увеличить RANGE_BAGGING до {RANGE_BAGGING + 0.1:0.1f}')


def validate_model_params(model_params: dict):
    """Проверяет наличие верных ключей в словаре, описывающем модель"""
    for key in model_params:
        if set(model_params[key]) != set(PARAM_SPACE[key]):
            raise ValueError(f'Неверный перечень ключей в разделе {key}')


def cv_model(params: dict, positions: tuple, date: pd.Timestamp):
    """Кросс-валидирует модель по RMSE

    Осуществляется проверка, что не достигнут максимум итераций, возвращается RMSE и параметры модели с оптимальным
    количеством итераций в формате целевой функции hyperopt

    Parameters
    ----------
    params
        Словарь с параметрами модели: ключ 'data' - параметры данных, ключ 'model' - параметры модели
    positions
        Кортеж тикеров, для которых необходимо осуществить кросс-валидацию
    date
        Дата, для которой необходимо осуществить кросс-валидацию
    Returns
    -------
    dict
        Словарь с результатом в формате hyperopt: ключ 'loss' - RMSE на кросс-валидации, 'status' - успешного
        прохождения оценки RMSE, ключ 'data' - параметры данных, ключ 'model' - параметры модели, в которые добавлено
        оптимальное количество итераций градиентного бустинга на кросс-валидации и вспомогательные настройки
    """
    validate_model_params(params)
    data_params = params['data']
    data = learn_pool(positions, date, **data_params)
    model_params = {}
    model_params.update(BASE_PARAMS)
    model_params.update(params['model'])
    scores = catboost.cv(pool=data,
                         params=model_params,
                         fold_count=FOLDS_COUNT)
    if len(scores) == MAX_ITERATIONS:
        raise ValueError(f'Необходимо увеличить MAX_ITERATIONS = {MAX_ITERATIONS}')
    index = scores['test-RMSE-mean'].idxmin()
    model_params['iterations'] = index + 1
    return dict(loss=scores.loc[index, 'test-RMSE-mean'],
                status=hyperopt.STATUS_OK,
                data=data_params,
                model=model_params)


def optimize_hyper(positions: tuple, date: pd.Timestamp):
    """Ищет и  возвращает лучший набор гиперпараметров без количества итераций"""
    objective = functools.partial(cv_model, positions=positions, date=date)
    best = hyperopt.fmin(objective,
                         space=PARAM_SPACE,
                         algo=hyperopt.tpe.suggest,
                         max_evals=MAX_SEARCHES,
                         rstate=np.random.RandomState(SEED))
    best_space = hyperopt.space_eval(PARAM_SPACE, best)
    check_space_bounds(best_space)
    return best_space


if __name__ == '__main__':
    DATE = '2018-09-03'
    pos = ('CHMF', 'RTKMP', 'SNGSP', 'VSMO', 'LKOH')
    MAX_SEARCHES = 2
    print(optimize_hyper(pos, pd.Timestamp(DATE)))
