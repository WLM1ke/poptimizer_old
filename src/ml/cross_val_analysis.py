"""Функции для проведения графического анализа кросс-валидации"""
from collections import namedtuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, explained_variance_score
from sklearn.model_selection import cross_val_predict, learning_curve, validation_curve, KFold
from sklearn.svm import LinearSVR

from ml.cases import Freq, all_cases, Cases

FIG_SIZE = 4
SHUFFLE = True
SEED = 284704


def draw_cross_val_predict(ax, regression, cases, cv):
    """График прогнозируемого с помощью кросс-валидации значения против фактического значения"""
    predicted = cross_val_predict(regression.estimator, cases.x, cases.y, groups=cases.groups, cv=cv)
    mse = mean_squared_error(cases.y, predicted)
    ev = explained_variance_score(cases.y, predicted)
    ax.set_title(f'{regression.estimator.__class__.__name__}'
                 f'\nMSE^0,5 = {mse ** 0.5:0.2%} / EV = {ev:0.2%}')
    ax.scatter(cases.y, predicted, edgecolors=(0, 0, 0))
    ax.plot([cases.y.min(), cases.y.max()], [cases.y.min(), cases.y.max()], 'k--', lw=1)
    ax.set_xlabel('Measured')
    ax.set_ylabel('Cross-Validated Prediction')


def draw_learning_curve(ax, regression, data, cv):
    """График кривой обучения в зависимости от размера выборки"""
    ax.set_title(f'Learning curve')
    ax.set_xlabel('Training examples')
    train_sizes, train_scores, test_scores = learning_curve(regression.estimator,
                                                            data.x,
                                                            data.y,
                                                            groups=data.groups,
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


def draw_validation_curve(ax, regression, cases, cv):
    """График кросс-валидации в зависимости от значения параметров модели"""
    train_scores, test_scores = validation_curve(regression.estimator,
                                                 cases.x,
                                                 cases.y,
                                                 regression.param_name,
                                                 regression.param_range,
                                                 cases.groups,
                                                 cv,
                                                 'neg_mean_squared_error')
    train_scores_mean = (-np.mean(train_scores, axis=1)) ** 0.5
    test_scores_mean = (-np.mean(test_scores, axis=1)) ** 0.5
    min_val = test_scores_mean.argmin()
    ax.grid()
    ax.set_title(f'Validation curve'
                 f'\nBest: {regression.param_name} - {regression.param_range[min_val]:0.2f} = '
                 f'{test_scores_mean.min():0.2%}')
    ax.set_xlabel(f'{regression.param_name}')
    lw = 2
    param_range = [str(i) for i in regression.param_range]
    ax.plot(param_range, train_scores_mean, label="Training score",
            color="r", lw=lw)
    ax.plot(param_range, test_scores_mean, label="Cross-validation score",
            color="g", lw=lw)
    ax.legend(loc="best")


RegressionCase = namedtuple('RegressionCase', 'estimator param_name param_range')


def draw_cross_val_analysis(regressions: list, cases: Cases):
    """Рисует графики для анализа кросс-валидации KFold для регрессий из списка

    Для каждой регрессии графики расположены в ряд. В каждом ряду как минимум два графика: прогнозируемого против
    фактического значения и кривая обучения в зависимости от размера выборки. При наличии param_name добавляется график
    кросс-валидации в зависимости от значения параметров модели

    Parameters
    ----------
    cases
        Данные для анализа
    regressions
        Список регрессий для анализа
    """
    rows = len(regressions)
    fig, ax_list = plt.subplots(rows, 3, figsize=(FIG_SIZE * 3, FIG_SIZE * rows), squeeze=False)
    fig.tight_layout(pad=3, h_pad=5)
    n_splits = len(set(cases.y.index.levels[0]))
    cv = KFold(n_splits=n_splits, shuffle=SHUFFLE, random_state=SEED)
    for row, regression in enumerate(regressions):
        draw_cross_val_predict(ax_list[row, 0], regression, cases, cv)
        draw_learning_curve(ax_list[row, 1], regression, cases, cv)
        if regression.param_name:
            draw_validation_curve(ax_list[row, 2], regression, cases, cv)
    plt.show()


if __name__ == '__main__':
    POSITIONS = dict(AKRN=563,
                     BANEP=488 + 19,
                     CHMF=234 + 28 + 8,
                     GMKN=146 + 29,
                     LKOH=340 + 18,
                     LSNGP=18,
                     LSRG=2346 + 64 + 80,
                     MSRS=128 + 117,
                     MSTT=1823,
                     MTSS=1383 + 36,
                     PMSBP=2873 + 418 + 336,
                     RTKMP=1726 + 382 + 99,
                     SNGSP=318,
                     TTLK=234,
                     UPRO=986 + 0 + 9,
                     VSMO=102,
                     PRTK=0,
                     MVID=0,
                     IRKT=0,
                     TATNP=0,
                     TATN=0)
    DATE = '2018-08-24'
    data_ = all_cases(tuple(key for key in POSITIONS), pd.Timestamp(DATE), Freq.monthly, 5)

    regressions_ = [RegressionCase(Ridge(alpha=0.01,
                                         random_state=SEED, max_iter=10000),
                                   'alpha',
                                   [10 ** (i - 4) for i in range(5)]),
                    RegressionCase(LinearSVR(epsilon=0.025, C=10,
                                             random_state=SEED, verbose=True, max_iter=10000),
                                   'C',
                                   [10 ** (i - 1) for i in range(5)]),
                    RegressionCase(GradientBoostingRegressor(n_estimators=100, subsample=0.99, max_depth=1,
                                                             learning_rate=0.08,
                                                             random_state=SEED, verbose=True),
                                   'learning_rate',
                                   [0.08 + (0.01 * (i - 2)) for i in range(5)])]

    clf = GradientBoostingRegressor(n_estimators=100, subsample=0.99, max_depth=1, learning_rate=0.08,
                                    random_state=SEED, verbose=True)
    clf.fit(data_.x, data_.y)
    print(clf.feature_importances_[:len(POSITIONS)])
    print(clf.feature_importances_[len(POSITIONS):])

    draw_cross_val_analysis(regressions_, data_)
