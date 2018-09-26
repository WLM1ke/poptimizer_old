"""Оптимизация гиперпараметров ML-модели"""
import functools

import catboost
import hyperopt
import numpy as np
import pandas as pd
from hyperopt import hp

# Базовые настройки catboost
MAX_ITERATIONS = 800
SEED = 284704
FOLDS_COUNT = 20
BASE_PARAMS = dict(iterations=MAX_ITERATIONS,
                   random_state=SEED,
                   od_type='Iter',
                   verbose=False,
                   allow_writing_files=False)

# Настройки hyperopt
MAX_SEARCHES = 100

# Рекомендации Яндекс - https://tech.yandex.com/catboost/doc/dg/concepts/parameter-tuning-docpage/

# OneHot кодировка - учитывая количество акций в портфеле используется cat-кодировка или OneHot-кодировка
ONE_HOT_SIZE = [2, 100]

# Скорость обучения
LEARNING_RATE_RANGE = 0.1

# Глубина деревьев
DEPTH_RANGE = 3

# L2-регуляризация
L2_RANGE = 0.1

# Случайность разбиений
RAND_STRENGTH_RANGE = 0.1

# Интенсивность бегинга
BAGGING_RANGE = 0.1


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


def make_model_space(params: dict):
    """Создает вероятностное пространство для параметров регрессии"""
    model = params['model']
    depths = [depth for depth in range(model['depth'] - DEPTH_RANGE, model['depth'] + DEPTH_RANGE + 1) if depth > 0]
    space = {
        'one_hot_max_size': make_choice_space('one_hot_max_size', ONE_HOT_SIZE),
        'learning_rate': make_log_space('learning_rate', model['learning_rate'], LEARNING_RATE_RANGE),
        'depth': make_choice_space('depth', depths),
        'l2_leaf_reg': make_log_space('l2_leaf_reg', model['l2_leaf_reg'], L2_RANGE),
        'random_strength': make_log_space('rand_strength', model['random_strength'], RAND_STRENGTH_RANGE),
        'bagging_temperature': make_log_space('bagging_temperature', model['bagging_temperature'], BAGGING_RANGE)}
    return space


def check_model_bounds(params: dict, base_params: dict):
    """Проверяет и дает рекомендации о расширении границ пространства поиска параметров

    Для целочисленных параметров - предупреждение выдается на границе диапазона и рекомендуется увеличить диапазон на 1.
    Для реальных параметров - предупреждение выдается в 10% от границе. Рекомендуется сместить центр поиска к текущему
    значению и расширить границы поиска на 10%
    """
    model = params['model']
    base_model = base_params['model']
    if abs(np.log(model['learning_rate'] / base_model['learning_rate'])) / np.log1p(LEARNING_RATE_RANGE) > 0.9:
        print(f'Необходимо увеличить RANGE_LEARNING_RATE до {LEARNING_RATE_RANGE + 0.1:0.1f}')

    if model['depth'] == base_model['depth'] - DEPTH_RANGE or model['depth'] == base_model['depth'] + DEPTH_RANGE:
        print(f'\nНеобходимо увеличить DEPTH_RANGE до {DEPTH_RANGE + 1}')

    if abs(np.log(model['l2_leaf_reg'] / base_model['l2_leaf_reg'])) / np.log1p(L2_RANGE) > 0.9:
        print(f'Необходимо увеличить RANGE_L2 до {L2_RANGE + 0.1:0.1f}')

    if abs(np.log(model['random_strength'] / base_model['random_strength'])) / np.log1p(RAND_STRENGTH_RANGE) > 0.9:
        print(f'Необходимо увеличить RANGE_RAND_STRENGTH до {RAND_STRENGTH_RANGE + 0.1:0.1f}')

    if abs(np.log(model['bagging_temperature'] / base_model['bagging_temperature'])) / np.log1p(BAGGING_RANGE) > 0.9:
        print(f'Необходимо увеличить RANGE_BAGGING до {BAGGING_RANGE + 0.1:0.1f}')


def cv_model(params: dict, positions: tuple, date: pd.Timestamp, data_pool):
    """Кросс-валидирует модель по RMSE, нормированному на СКО набора данных

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
    data_pool
        Функция для получения catboost.Pool с данными
    Returns
    -------
    dict
        Словарь с результатом в формате hyperopt: ключ 'loss' - нормированная RMSE на кросс-валидации,
        'status' - успешного прохождения, ключ 'std' - RMSE на кросс-валидации, ключ 'r2' - нормированная RMSE на
        кросс-валидации, ключ 'data' - параметры данных, ключ 'model' - параметры модели, в которые добавлено
        оптимальное количество итераций градиентного бустинга на кросс-валидации и вспомогательные настройки
    """
    data_params = params['data']
    data = data_pool(positions, date, **data_params)
    pool_std = np.array(data.get_label()).std()
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
    return dict(loss=scores.loc[index, 'test-RMSE-mean'] / pool_std,
                status=hyperopt.STATUS_OK,
                std=scores.loc[index, 'test-RMSE-mean'],
                r2=1 - (scores.loc[index, 'test-RMSE-mean'] / pool_std) ** 2,
                data=data_params,
                model=model_params)


def optimize_hyper(param_space: dict, positions: tuple, date: pd.Timestamp, data_pool):
    """Ищет и  возвращает лучший набор гиперпараметров без количества итераций"""
    objective = functools.partial(cv_model, positions=positions, date=date, data_pool=data_pool)
    best = hyperopt.fmin(objective,
                         space=param_space,
                         algo=hyperopt.tpe.suggest,
                         max_evals=MAX_SEARCHES,
                         rstate=np.random.RandomState(SEED))
    best_space = hyperopt.space_eval(param_space, best)
    return best_space
