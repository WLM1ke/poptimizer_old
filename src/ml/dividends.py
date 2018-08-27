"""Ожидаемая дивидендная доходность методами ML"""
import functools

import pandas as pd
from scipy.stats import reciprocal
from sklearn.linear_model import Ridge
from sklearn.metrics import explained_variance_score
from sklearn.model_selection import KFold, RandomizedSearchCV, cross_validate, cross_val_predict

from ml.cases import Freq, all_cases

SEED = 284704
CLF = Ridge(random_state=SEED, max_iter=10000)
RANGE = 10
VERBOSE = True


class DividendsML:
    """Автоматический подбор параметров для ML и расчет ожидаемой дивидендной доходности и СКО"""

    def __init__(self, tickers: tuple, date: pd.Timestamp, alpha: float = 1, freq: Freq = Freq.monthly, lags: int = 5):
        self._tickers = tickers
        self._date = date
        self._freq = freq
        self._lags = lags
        cases = all_cases(tickers, date, freq, lags)
        self._clf = CLF.set_params(alpha=alpha)
        cv = KFold(n_splits=len(set(cases.y.index.levels[0])), shuffle=True, random_state=SEED)
        scores = cross_validate(estimator=self._clf,
                                X=cases.x,
                                y=cases.y,
                                groups=cases.groups,
                                scoring='neg_mean_squared_error',
                                cv=cv,
                                n_jobs=-1,
                                verbose=VERBOSE)
        self._mse = scores['test_score'].mean()

        while True:
            reciprocal.rvs = functools.partial(reciprocal.rvs, a=alpha / RANGE, b=alpha * RANGE, random_state=SEED)
            search_cv = RandomizedSearchCV(estimator=self._clf,
                                           param_distributions={'alpha': reciprocal},
                                           scoring='neg_mean_squared_error',
                                           n_jobs=-1,
                                           cv=cv,
                                           refit=True,
                                           verbose=VERBOSE,
                                           random_state=SEED)
            search_cv.fit(cases.x, cases.y, cases.groups)
            if search_cv.best_score_ < self._mse:
                break
            alpha = search_cv.best_params_['alpha']
            self._clf = search_cv.best_estimator_
            self._mse = search_cv.best_score_
        predicted = cross_val_predict(estimator=self._clf,
                                      X=cases.x,
                                      y=cases.y,
                                      groups=cases.groups,
                                      cv=cv,
                                      n_jobs=-1,
                                      verbose=VERBOSE)
        self._explained_variance = explained_variance_score(cases.y, predicted)

    @property
    def clf(self):
        return self._clf

    @property
    def std(self):
        return (-self._mse) ** 0.5

    @property
    def explained_variance(self):
        return self._explained_variance


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
    div = DividendsML(tuple(key for key in POSITIONS), pd.Timestamp(DATE))
    print(div.clf)
    print(div.std)
    print(div.explained_variance)
