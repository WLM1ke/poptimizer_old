"""Ожидаемая дивидендная доходность методами ML"""
import functools

import pandas as pd
from scipy.stats import reciprocal
from sklearn.linear_model import Ridge
from sklearn.metrics import explained_variance_score, mean_squared_error
from sklearn.model_selection import KFold, RandomizedSearchCV, cross_validate, cross_val_predict

from ml.cases import Freq, all_cases

SEED = 284704
CLF = Ridge(random_state=SEED, max_iter=10000)
ALPHA = 0.01
RANGE = 10
VERBOSE = True



class DividendsML:
    """Автоматический подбор параметров для ML, расчет ожидаемой дивидендной доходности и СКО"""

    def __init__(self, tickers: tuple, date: pd.Timestamp, freq: Freq = Freq.monthly, lags: int = 5):
        """Осуществляет поиск оптимального параметра регуляризации для гребневой регрессии

        Parameters
        ----------
        tickers
            Набор тикеров для построения ML-модели
        date
            Дата, для которой необходимо построить ML-модель
        freq
            Частота данных для построения ML-модели
        lags
            Количество лагов дивидендной доходности для построения ML-модели
        """
        self._tickers = tickers
        self._date = date
        self._freq = freq
        self._lags = lags
        self._cases = all_cases(tickers, date, freq, lags)
        self._clf = CLF.set_params(alpha=ALPHA)
        self._cv = KFold(n_splits=len(set(self._cases.y.index.levels[0])), shuffle=True, random_state=SEED)
        scores = cross_validate(estimator=self._clf,
                                X=self._cases.x,
                                y=self._cases.y,
                                groups=self._cases.groups,
                                scoring='neg_mean_squared_error',
                                cv=self._cv,
                                n_jobs=-1,
                                verbose=VERBOSE)
        self._optimize_alpha(scores['test_score'].mean())

    def _optimize_alpha(self, score):
        """Ищет альфу и сохраняет ML-модель, минимизирующую СКО на кросс-валидации"""
        cases = self._cases
        alpha = self._clf.get_params()['alpha']
        while True:
            reciprocal.rvs = functools.partial(reciprocal.rvs, a=alpha / RANGE, b=alpha * RANGE, random_state=SEED)
            search_cv = RandomizedSearchCV(estimator=self._clf,
                                           param_distributions={'alpha': reciprocal},
                                           scoring='neg_mean_squared_error',
                                           n_jobs=-1,
                                           cv=self._cv,
                                           refit=True,
                                           verbose=VERBOSE,
                                           random_state=SEED)
            search_cv.fit(cases.x, cases.y, cases.groups)
            if search_cv.best_score_ < score:
                break
            alpha = search_cv.best_params_['alpha']
            self._clf = search_cv.best_estimator_
            score = search_cv.best_score_

    @property
    def clf(self):
        """Оптимальный классификатор"""
        return self._clf

    @property
    def _predicted(self):
        """Кросс-валидированные прогнозные значения для кейсов - используются для расчета метрик"""
        return cross_val_predict(estimator=self._clf,
                                 X=self._cases.x,
                                 y=self._cases.y,
                                 groups=self._cases.groups,
                                 cv=self._cv,
                                 n_jobs=-1,
                                 verbose=VERBOSE)

    @property
    def std(self):
        """СКО прогноза на кросс-валидации"""
        return (mean_squared_error(self._cases.y, self._predicted)) ** 0.5

    @property
    def explained_variance(self):
        """Объясненная дисперсия на кросс-валидации"""
        return explained_variance_score(self._cases.y, self._predicted)


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
