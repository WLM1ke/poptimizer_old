"""Кросс-валидация и оптимизация гиперпараметров ML-модели"""
import functools

import catboost
import hyperopt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hyperopt import hp
from sklearn import model_selection

# Размер графика с кривой обучения
FIG_SIZE = 8

# Базовые настройки catboost
MAX_ITERATIONS = 1000
SEED = 284704
FOLDS_COUNT = 20
TECH_PARAMS = dict(iterations=MAX_ITERATIONS,
                   random_state=SEED,
                   od_type='Iter',
                   verbose=False,
                   allow_writing_files=False)

# Настройки hyperopt
MAX_SEARCHES = 100

# Диапазоны поиска ключевых гиперпараметров относительно базового значения параметров
# Рекомендации Яндекс - https://tech.yandex.com/catboost/doc/dg/concepts/parameter-tuning-docpage/

# OneHot кодировка - учитывая количество акций в портфеле используется cat-кодировка или OneHot-кодировка
ONE_HOT_SIZE = [2, 100]

# Диапазон поиска скорости обучения - catboost не поддерживает скорость обучения больше 1
LR_RANGE = 0.3
LR_UPPER_LIMIT = 1.0

# Ограничение на максимальную глубину деревьев
MAX_DEPTH = 8

# Диапазон поиска параметра L2-регуляризации
L2_RANGE = 0.9

# Диапазон поиска случайности разбиений
RAND_STRENGTH_RANGE = 1.0

# Диапазон поиска интенсивности бегинга
BAGGING_RANGE = 1.3


def log_limits(middle: float, percent_range: float, upper_limit: float = None):
    """Логарифмический интервал"""
    log_x = np.log(middle)
    log_delta = np.log1p(percent_range)
    if upper_limit:
        return log_x - log_delta, min(log_x + log_delta, upper_limit)
    return log_x - log_delta, log_x + log_delta


def make_log_space(space_name: str, middle: float, percent_range: float, upper_limit: float = None):
    """Создает логарифмическое вероятностное пространство"""
    lower, upper = log_limits(middle, percent_range, upper_limit)
    return hp.loguniform(space_name, lower, upper)


def make_choice_space(space_name: str, choice):
    """Создает вероятностное пространство для выбора из нескольких вариантов"""
    return hp.choice(space_name, list(choice))


def make_model_space(params: dict):
    """Создает вероятностное пространство для параметров регрессии"""
    model = params['model']
    space = {
        'one_hot_max_size': make_choice_space('one_hot_max_size', ONE_HOT_SIZE),
        'ignored_features': model['ignored_features'],
        'learning_rate': make_log_space('learning_rate', model['learning_rate'], LR_RANGE, LR_UPPER_LIMIT),
        'depth': make_choice_space('depth', range(1, MAX_DEPTH + 1)),
        'l2_leaf_reg': make_log_space('l2_leaf_reg', model['l2_leaf_reg'], L2_RANGE),
        'random_strength': make_log_space('rand_strength', model['random_strength'], RAND_STRENGTH_RANGE),
        'bagging_temperature': make_log_space('bagging_temperature', model['bagging_temperature'], BAGGING_RANGE)}
    return space


def check_model_bounds(params: dict, base_params: dict):
    """Проверяет и дает рекомендации о расширении границ пространства поиска параметров

    Для целочисленных параметров - предупреждение выдается на границе диапазона и рекомендуется увеличить диапазон на 1.
    Для реальных параметров - предупреждение выдается в 10% от границе и рекомендуется расширить границы поиска на 10%
    """
    model = params['model']
    base_model = base_params['model']
    if abs(np.log(model['learning_rate'] / base_model['learning_rate'])) / np.log1p(LR_RANGE) > 0.9:
        print(f'\nНеобходимо увеличить LR_RANGE до {LR_RANGE + 0.1:0.1f}')

    if model['depth'] == MAX_DEPTH:
        print(f'\nНеобходимо увеличить MAX_DEPTH до {MAX_DEPTH + 1}')

    if abs(np.log(model['l2_leaf_reg'] / base_model['l2_leaf_reg'])) / np.log1p(L2_RANGE) > 0.9:
        print(f'\nНеобходимо увеличить L2_RANGE до {L2_RANGE + 0.1:0.1f}')

    if abs(np.log(model['random_strength'] / base_model['random_strength'])) / np.log1p(RAND_STRENGTH_RANGE) > 0.9:
        print(f'\nНеобходимо увеличить RAND_STRENGTH_RANGE до {RAND_STRENGTH_RANGE + 0.1:0.1f}')

    if abs(np.log(model['bagging_temperature'] / base_model['bagging_temperature'])) / np.log1p(BAGGING_RANGE) > 0.9:
        print(f'\nНеобходимо увеличить BAGGING_RANGE до {BAGGING_RANGE + 0.1:0.1f}')


def make_model_params(params):
    """Объединяет технические и конкретные параметры модели"""
    model_params = {}
    model_params.update(TECH_PARAMS)
    model_params.update(params['model'])
    return model_params


def cv_model(params: dict, positions: tuple, date: pd.Timestamp, data_pool_func):
    """Кросс-валидирует модель по RMSE, нормированному на СКО набора данных
    Осуществляется проверка, что не достигнут максимум итераций, возвращается RMSE, R2 и параметры модели с оптимальным
    количеством итераций в формате целевой функции hyperopt
    Parameters
    ----------
    params
        Словарь с параметрами модели: ключ 'data' - параметры данных, ключ 'model' - параметры модели
    positions
        Кортеж тикеров, для которых необходимо осуществить кросс-валидацию
    date
        Дата, для которой необходимо осуществить кросс-валидацию
    data_pool_func
        Функция для получения catboost.Pool с данными
    Returns
    -------
    dict
        Словарь с результатом в формате hyperopt:
        ключ 'loss' - нормированная RMSE на кросс-валидации (для hyperopt),
        ключ 'status' - успешного прохождения (для hyperopt),
        ключ 'std' - RMSE на кросс-валидации,
        ключ 'r2' - 1- нормированная RMSE на кросс-валидации в квадрате,
        ключ 'data' - параметры данных,
        ключ 'model' - параметры модели, в которые добавлено оптимальное количество итераций градиентного бустинга на
        кросс-валидации и общие настройки
    """
    data_params = params['data']
    data = data_pool_func(positions, date, **data_params)
    pool_std = np.array(data.get_label()).std()
    model_params = make_model_params(params)
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


def learning_curve(params: dict, positions: tuple, date: pd.Timestamp, data_pool_params, fractions: tuple):
    """Рисует кривую обучения для train_sizes долей от общего Pool данных

    Parameters
    ----------
    params
        Словарь с параметрами модели: ключ 'data' - параметры данных, ключ 'model' - параметры модели, который должен
        содержать количество итераций
    positions
        Кортеж тикеров, для которых необходимо построить кривую обучения
    date
        Дата, для которой необходимо построить кривую обучения
    data_pool_params
        Функция для получения параметров для построения catboost.Pool с данными
    fractions
        Список с возрастающими долями от общей выборки, которые будут использоваться для построения кривой обучения
    """
    data_params = params['data']
    pool_params = data_pool_params(positions, date, **data_params)
    model_params = make_model_params(params)
    model_params['cat_features'] = pool_params['cat_features']
    train_sizes, train_scores, test_scores = model_selection.learning_curve(
        catboost.CatBoostRegressor(**model_params),
        pool_params['data'],
        pool_params['label'],
        train_sizes=list(fractions),
        cv=FOLDS_COUNT,
        scoring='neg_mean_squared_error',
        shuffle=True,
        random_state=SEED)
    fig, ax = plt.subplots(figsize=(FIG_SIZE, FIG_SIZE))
    fig.tight_layout(pad=3, h_pad=5)
    ax.set_title(f'Learning curve')
    ax.set_xlabel('Training examples')
    train_scores_mean = (-np.mean(train_scores, axis=1)) ** 0.5
    test_scores_mean = (-np.mean(test_scores, axis=1)) ** 0.5
    ax.grid()
    ax.plot(train_sizes, train_scores_mean, 'o-', color="r",
            label="Training score")
    ax.plot(train_sizes, test_scores_mean, 'o-', color="g",
            label="Cross-validation score")
    ax.legend(loc="best")
    plt.show()
    return train_sizes, train_scores_mean, test_scores_mean


def optimize_hyper(base_params: dict, positions: tuple, date: pd.Timestamp, data_pool_func, data_space: dict):
    """Ищет и  возвращает лучший набор гиперпараметров без количества итераций в окрестности базового набора параметров

    Parameters
    ----------
    base_params
        Параметры, в окрестностях которых осуществляется поиск оптимума
    positions
        Кортеж тикеров, для которых необходимо осуществляется поиск оптимума
    date
        Дата, до которой используются данные
    data_pool_func
        Функция получения данных для тренировки модели
    data_space
        Функция для формирования пространства поиска вариантов данных для модели
    Returns
    -------
    dict
        ключ 'data' - параметры данных,
        ключ 'model' - параметры модели без количества итераций градиентного бустинга
    """
    objective = functools.partial(cv_model, positions=positions, date=date, data_pool_func=data_pool_func)
    param_space = dict(data=data_space,
                       model=make_model_space(base_params))
    best = hyperopt.fmin(objective,
                         space=param_space,
                         algo=hyperopt.tpe.suggest,
                         max_evals=MAX_SEARCHES,
                         rstate=np.random.RandomState(SEED))
    # Преобразование из внутреннего представление в исходное пространство
    best_params = hyperopt.space_eval(param_space, best)
    check_model_bounds(best_params, base_params)
    return best_params
