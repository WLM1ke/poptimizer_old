"""Функции дл] проведения графического анализа кросс-валидации"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict, learning_curve, validation_curve

from ml.cases import all_cases

SHUFFLE = False
SEED = 284704


def draw_cross_val_predict(ax, regression, x, y, groups, cv):
    """График прогнозируемого с помощью кросс-валидации значения против фактического значения"""
    predicted = cross_val_predict(regression, x, y, groups=groups, cv=cv)
    mse = mean_squared_error(y, predicted)
    ax.set_title(f'{regression.__class__.__name__} - {cv.__class__.__name__}'
                 f'\nMSE^0,5 = {mse ** 0.5:0.2f}')
    ax.scatter(y, predicted, edgecolors=(0, 0, 0))
    ax.plot([y.min(), y.max()], [y.min(), y.max()], 'k--', lw=1)
    ax.set_xlabel('Measured')
    ax.set_ylabel('Predicted')


def draw_learning_curve(ax, regression, x, y, groups, cv):
    """График кривой обучения в зависимости от размера выборки"""
    ax.set_title(f'Learning curve - {regression.__class__.__name__}')
    ax.set_xlabel('Training examples')
    train_sizes, train_scores, test_scores = learning_curve(regression, x, y,
                                                            groups=groups,
                                                            cv=cv,
                                                            scoring='neg_mean_squared_error',
                                                            shuffle=SHUFFLE,
                                                            random_state=SEED)
    train_scores_mean = (-np.mean(train_scores, axis=1)) ** 0.5
    test_scores_mean = (-np.mean(test_scores, axis=1)) ** 0.5
    ax.grid()
    ax.plot(train_sizes, train_scores_mean, 'o-', color="r",
            label="Training score")
    ax.plot(train_sizes, test_scores_mean, 'o-', color="g",
            label="Cross-validation score")
    ax.legend(loc="best")


def draw_validation_curve(ax, regression, x, y, groups, cv, param_name, param_range):
    """График кросс-валидации в зависимости от значения параметров модели"""
    train_scores, test_scores = validation_curve(regression, x, y,
                                                 param_name, param_range,
                                                 groups, cv,
                                                 'neg_mean_squared_error')
    train_scores_mean = (-np.mean(train_scores, axis=1)) ** 0.5
    test_scores_mean = (-np.mean(test_scores, axis=1)) ** 0.5
    min_val = test_scores_mean.argmin()
    ax.grid()
    ax.set_title(f'Validation curve - {regression.__class__.__name__}'
                 f'\nMin: {param_name} - {param_range[min_val]} = {test_scores_mean.min():0.2f}')
    ax.set_xlabel(f'{param_name}')
    lw = 2
    ax.plot(param_range, train_scores_mean, label="Training score",
            color="r", lw=lw)
    ax.plot(param_range, test_scores_mean, label="Cross-validation score",
            color="g", lw=lw)
    ax.legend(loc="best")


def draw_measured_vs_predicted(regression, x, y, groups, param_name=None, param_range=None):
    """Рисует графики для анализа кросс-валидации LeaveOneGroupOut

    В каждом ряду как минимум два графика: прогнозируемого против фактического значения и кривая обучения в зависимости
    от размера выборки. При наличии param_name добавляется график кросс-валидации в зависимости от значения параметров
    модели

    Parameters
    ----------
    regression
        Регрессионная модель
    x
        Переменные x
    y
        Переменная y
    groups
        Группы для LeaveOneGroupOut кросс-валидации
    param_name
        Параметр для выбора оптимального
    param_range
        Массив значений параметра
    """
    if param_name:
        _, ax_list = plt.subplots(1, 3, figsize=(18, 6), squeeze=False)

    else:
        _, ax_list = plt.subplots(1, 2, figsize=(12, 6), squeeze=False)
    group_cv = LeaveOneGroupOut()
    for row, cv in enumerate([group_cv]):
        draw_cross_val_predict(ax_list[row, 0], regression, x, y, groups, cv)
        draw_learning_curve(ax_list[row, 1], regression, x, y, groups, cv)
        if param_name:
            draw_validation_curve(ax_list[row, 2], regression, x, y, groups, cv, param_name, param_range)
    plt.show()


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
                     ALRS=0)
    cases = all_cases(tuple(key for key in POSITIONS), pd.Timestamp('2018-08-16'))
    cases.reset_index(inplace=True)
    y_ = cases.iloc[:, -1] * 100
    x_ = cases.iloc[:, 2:-1] * 100
    groups_ = cases.iloc[:, 0]
    regression_ = DummyRegressor(strategy='mean')
    draw_measured_vs_predicted(regression_, x_, y_, groups_, 'strategy', ['mean', 'median'])
