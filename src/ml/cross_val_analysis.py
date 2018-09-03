"""Функции для проведения графического анализа кросс-валидации"""
from collections import namedtuple

import catboost
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_squared_error, explained_variance_score
from sklearn.model_selection import cross_val_predict, learning_curve, validation_curve, KFold

from ml.cases import Freq, learn_pool

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


def draw_cross_val_analysis(regressions: list, cases):
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
                     TATNP=0)
    DATE = '2018-08-31'
    print(DATE)
    print('')

    min_std = None
    saved = None
    pos = tuple(key for key in POSITIONS)
    for lag in range(1, 4):
        for freq in Freq:
            data, _ = learn_pool(pos, pd.Timestamp(DATE), freq, lag)
            for depth in range(1, 12):
                params = dict(depth=depth,
                              random_state=SEED,
                              learning_rate=0.1,
                              verbose=False,
                              allow_writing_files=False,
                              od_type='Iter',
                              use_best_model=True)
                scores = catboost.cv(pool=data,
                                     params=params,
                                     fold_count=20)
                index = scores.iloc[:, 0].idxmin()
                score = scores.iloc[index, 0]
                score_std = scores.iloc[index, 1]
                if min_std is None or score < min_std:
                    min_std = score
                    saved = freq, lag, depth, index
                    print(
                        f'{lag} {str(freq).ljust(14)} {depth} {str(index + 1).ljust(3)} '
                        f'{score:0.4%} {score_std:0.4%}')

    data, pred = learn_pool(pos, pd.Timestamp(DATE), saved[0], saved[1])
    params = dict(depth=saved[2],
                  iterations=saved[3],
                  random_state=SEED,
                  learning_rate=0.1,
                  verbose=False,
                  od_type='Iter',
                  allow_writing_files=False)
    clf = CatBoostRegressor(**params)
    clf.fit(data)
    print('')
    print(pd.Series(clf.predict(pred), list(pos)))
    print('')
    print(clf.feature_importances_)

    """
    2018-08-31
    
    1 Freq.monthly   1 86  4.9647% 0.5780%
    1 Freq.monthly   2 68  4.9550% 0.5829%
    1 Freq.quarterly 1 90  4.6627% 1.0223%
    1 Freq.quarterly 2 56  4.6480% 1.0320%
    1 Freq.quarterly 3 70  4.6468% 1.0259%
    1 Freq.quarterly 8 62  4.6456% 1.0550%
    1 Freq.yearly    1 42  4.5854% 2.0081%
    1 Freq.yearly    2 53  4.5796% 1.9546%
    1 Freq.yearly    3 40  4.4914% 1.9026%
    2 Freq.yearly    7 57  4.4434% 2.5668%
    """
