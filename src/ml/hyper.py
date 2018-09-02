"""Оптимизация гиперпараметров ML-модели дивидендов"""
import functools
import pprint

import catboost
import hyperopt
import numpy as np
import pandas as pd
from hyperopt import hp

from ml.cases import Freq, learn_predict_pools

MAX_ITERATIONS = 1000
SEED = 284704
FOLDS_COUNT = 20
MAX_SEARCHES = 100
BASE_PARAMS = dict(iterations=MAX_ITERATIONS,
                   random_state=SEED,
                   od_type='Iter',
                   verbose=False,
                   allow_writing_files=False)

# Лаги
MAX_LAG = 3
# Рекомендации Яндекс - https://tech.yandex.com/catboost/doc/dg/concepts/parameter-tuning-docpage/
# OneHot кодировка - учитывая количество акций в портфеле используется cat-кодировка или OneHot-кодировка
ONE_HOT_SIZE = [2, 100]
# Скорость обучения
MEAN_LEARNING_RATE = 0.1
RANGE_LEARNING_RATE = 0.1
MIN_LEARNING_RATE = np.log(MEAN_LEARNING_RATE) - np.log1p(RANGE_LEARNING_RATE)
MAX_LEARNING_RATE = np.log(MEAN_LEARNING_RATE) + np.log1p(RANGE_LEARNING_RATE)
# Глубина деревьев
MAX_DEPTH = 8
# L2-регуляризация
MEAN_L2 = 2.7
RANGE_L2 = 0.2
MIN_L2 = np.log(MEAN_L2) - np.log1p(RANGE_L2)
MAX_L2 = np.log(MEAN_L2) + np.log1p(RANGE_L2)
# Случайность разбиений
MEAN_RAND_STRENGTH = 1.1
RANGE_RAND_STRENGTH = 0.2
MIN_RAND_STRENGTH = np.log(MEAN_RAND_STRENGTH) - np.log1p(RANGE_RAND_STRENGTH)
MAX_RAND_STRENGTH = np.log(MEAN_RAND_STRENGTH) + np.log1p(RANGE_RAND_STRENGTH)
# Интенсивность бегинга
MEAN_BAGGING = 0.9
RANGE_BAGGING = 0.2
MIN_BAGGING = np.log(MEAN_BAGGING) - np.log1p(RANGE_BAGGING)
MAX_BAGGING = np.log(MEAN_BAGGING) + np.log1p(RANGE_BAGGING)

PARAM_SPACE = {
    'data': {'freq': hp.choice('freq', [freq for freq in Freq]),
             'lags': hp.choice('lags', list(range(1, MAX_LAG + 1)))},
    'model': {'one_hot_max_size': hp.choice('one_hot_max_size', ONE_HOT_SIZE),
              'learning_rate': hp.loguniform('learning_rate', MIN_LEARNING_RATE, MAX_LEARNING_RATE),
              'depth': hp.choice('depth', list(range(1, MAX_DEPTH + 1))),
              'l2_leaf_reg': hyperopt.hp.loguniform('l2_leaf_reg', MIN_L2, MAX_L2),
              'random_strength': hyperopt.hp.loguniform('rand_strength', MIN_RAND_STRENGTH, MAX_RAND_STRENGTH),
              'bagging_temperature': hyperopt.hp.loguniform('bagging_temperature', MIN_BAGGING, MAX_BAGGING)}}


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
        оптимальное количество итераций градиентного бустинга на кросс-валидации
    """
    data_params = params['data']
    data, _ = learn_predict_pools(positions, date, **data_params)
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


def check_space_bounds(space: dict):
    """Проверяет и дает рекомендации о расширении границ поиска

    Для целочисленных параметров - предупреждение выдается на границе диапазона и рекомендуется увеличить диапазон на 1.
    Для реальных параметров - предупреждение выдается в 10% от границе. Рекомендуется сместить центр поиска к текущему
    значению и расширить границы поиска на 10%
    """
    if space['data']['lags'] == MAX_LAG:
        print(f'\nНеобходимо увеличить MAX_LAG до {MAX_LAG + 1}')

    if abs(np.log(space['model']['learning_rate']) - np.log(MEAN_LEARNING_RATE)) / np.log1p(RANGE_LEARNING_RATE) > 0.9:
        print(f"\nНеобходимо изменить MEAN_LEARNING_RATE на {space['model']['learning_rate']:0.2f}")
        print(f'Необходимо увеличить RANGE_LEARNING_RATE до {RANGE_LEARNING_RATE + 0.1:0.1f}')

    if space['model']['depth'] == MAX_DEPTH:
        print(f'\nНеобходимо увеличить MAX_DEPTH до {MAX_DEPTH + 1}')

    if abs(np.log(space['model']['l2_leaf_reg']) - np.log(MEAN_L2)) / np.log1p(RANGE_L2) > 0.9:
        print(f"\nНеобходимо изменить MEAN_L2 на {space['model']['l2_leaf_reg']:0.1f}")
        print(f'Необходимо увеличить RANGE_L2 до {RANGE_L2 + 0.1:0.1f}')

    if abs(np.log(space['model']['random_strength']) - np.log(MEAN_RAND_STRENGTH)) / np.log1p(
            RANGE_RAND_STRENGTH) > 0.9:
        print(f"\nНеобходимо изменить MEAN_RAND_STRENGTH на {space['model']['random_strength']:0.1f}")
        print(f'Необходимо увеличить RANGE_RAND_STRENGTH до {RANGE_RAND_STRENGTH + 0.1:0.1f}')

    if abs(np.log(space['model']['bagging_temperature']) - np.log(MEAN_BAGGING)) / np.log1p(RANGE_BAGGING) > 0.9:
        print(f"\nНеобходимо изменить MEAN_BAGGING на {space['model']['bagging_temperature']:0.1f}")
        print(f'Необходимо увеличить RANGE_BAGGING до {RANGE_BAGGING + 0.1:0.1f}')


def optimize_hyper(positions: tuple, date: pd.Timestamp):
    """Ищет и  возвращает лучший набор гиперпараметров"""
    objective = functools.partial(cv_model, positions=positions, date=date)
    best = hyperopt.fmin(objective,
                         space=PARAM_SPACE,
                         algo=hyperopt.tpe.suggest,
                         max_evals=MAX_SEARCHES,
                         rstate=np.random.RandomState(SEED))
    best_space = hyperopt.space_eval(PARAM_SPACE, best)
    check_space_bounds(best_space)
    return objective(best_space)


def find_better_model(base_model: dict, positions: tuple, date: pd.Timestamp):
    """Ищет оптимальную модель и сравнивает с базовой - результаты сравнения распечатываются

    Parameters
    ----------
    base_model
        Словарь описывающий параметры базовой модели
    positions
        Кортеж тикеров, для которых необходимо осуществить сравнение
    date
        Дата, для которой необходимо осуществить сравнение
    """
    best = optimize_hyper(positions, date)
    base = cv_model(base_model, positions, date)
    if base['loss'] < best['loss']:
        print('\nЛУЧШАЯ МОДЕЛЬ - Базовая модель')
        pprint.pprint(base, indent=1)
        print('\nНайденная модель')
        pprint.pprint(best, indent=1)
    else:
        print('\nЛУЧШАЯ МОДЕЛЬ - Найденная модель')
        pprint.pprint(best, indent=1)
        print('\nБазовая модель')
        pprint.pprint(base, indent=1)


if __name__ == '__main__':
    POSITIONS = dict(AKRN=563,
                     BANEP=488,
                     CHMF=234,
                     GMKN=146,
                     LKOH=340,
                     LSNGP=18,
                     LSRG=2346,
                     MSRS=128,
                     MSTT=1823,
                     MTSS=1383,
                     PMSBP=2873,
                     RTKMP=1726,
                     SNGSP=318,
                     TTLK=234,
                     UPRO=986,
                     VSMO=102,
                     PRTK=0,
                     MVID=0,
                     IRKT=0,
                     TATNP=0)
    DATE = '2018-08-31'
    pos = tuple(key for key in POSITIONS)
    base_model_ = {
        'data': {'freq': Freq.yearly,
                 'lags': 2},
        'model': {'iterations': 57,
                  'depth': 7,
                  'one_hot_max_size': 2,
                  'learning_rate': 0.1,
                  'l2_leaf_reg': 3,
                  'random_strength': 1,
                  'bagging_temperature': 1,
                  'allow_writing_files': False,
                  'od_type': 'Iter',
                  'random_state': 284704,
                  'verbose': False}}
    find_better_model(base_model_, pos, pd.Timestamp(DATE))
