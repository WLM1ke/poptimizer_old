"""Ожидаемая дивидендная доходность методами ML"""
import pandas as pd
from catboost import CatBoostRegressor
from scipy.stats import randint
from sklearn.metrics import explained_variance_score, mean_squared_error
from sklearn.model_selection import KFold, cross_validate, cross_val_predict, GridSearchCV

from ml.cases import Freq, learn_predict_pools

VERBOSE = True
SEED = 284704
PARAMS = dict(iterations=100, depth=6,
              learning_rate=0.1,
              od_type='Iter',
              early_stopping_rounds=10,
              verbose=False, random_state=SEED)


class DividendsML:
    """Автоматический подбор параметров для ML-модели, расчет ожидаемой дивидендной доходности и СКО"""
    _clf_class = CatBoostRegressor

    def __init__(self, clf_params: dict, tickers: tuple, date: pd.Timestamp, freq: Freq = Freq.monthly, lags: int = 5):
        """Осуществляет поиск оптимальных параметров для ML-модели

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
        self._clf_params = clf_params
        self._tickers = tickers
        self._date = date
        self._freq = freq
        self._lags = lags
        self._cases = learn_predict_pools(tickers, date, freq, lags)
        self._clf = self._clf_class(**clf_params)
        self._cv = KFold(n_splits=len(set(self._cases.y.index.levels[0])), shuffle=True, random_state=SEED)
        scores = cross_validate(self._clf,
                                self._cases.x,
                                self._cases.y,
                                self._cases.groups,
                                scoring='neg_mean_squared_error',
                                cv=self._cv,
                                n_jobs=-1,
                                verbose=VERBOSE)
        self._optimize_params(scores['test_score'].mean())

    def _optimize_params(self, score):
        """Ищет параметры и сохраняет ML-модель, минимизирующую СКО на кросс-валидации"""
        cases = self._cases
        while True:
            param_distributions = self._set_param_distributions()
            print(param_distributions)
            search_cv = GridSearchCV(estimator=self._clf,
                                     param_grid=param_distributions,
                                     scoring='neg_mean_squared_error',
                                     n_jobs=-1,
                                     cv=self._cv,
                                     refit=True,
                                     verbose=VERBOSE)
            search_cv.fit(cases.x, cases.y, cases.groups)
            if search_cv.best_score_ <= score:
                break
            self._clf = search_cv.best_estimator_
            score = search_cv.best_score_
            if VERBOSE:
                print('Основные параметры -', self.clf_params)
                print('СКО - ', (-score) ** 0.5)

    def _set_param_distributions(self):
        params = self._clf.get_params()
        param_distributions = dict()

        low = max(1, int(0.6 * params['iterations']))
        high = int(1.4 * params['iterations']) + 1
        param_distributions['iterations'] = randint.rvs(low, high, size=5)

        low = max(1, params['depth'] - 2)
        high = params['depth'] + 2
        param_distributions['depth'] = list(range(low, high + 1))

        return param_distributions

    @property
    def clf(self):
        """Оптимальный классификатор"""
        return self._clf

    @property
    def clf_params(self):
        """Параметры классификатора"""
        params = self.clf.get_params()
        return {k: params[k] for k in ['iterations', 'depth']}

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
    def mean(self):
        """Ожидаемые дивиденды"""
        clf = self._clf
        cases = self._cases
        clf.fit(cases.x, cases.y)
        prediction = clf.predict(cases.x_predict)
        return pd.Series(data=prediction, index=cases.x_predict.index.droplevel(0))

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
                     TATNP=0,
                     TATN=0)
    DATE = '2018-06-28'
    div = DividendsML(PARAMS, tuple(key for key in POSITIONS), pd.Timestamp(DATE), freq=Freq.quarterly, lags=1)
    print(div.clf_params)
    print('СКО -', div.std)
    print('Объясненная дисперсия -', div.explained_variance)
    print('Количество кейсов -', len(div._cases.x))
    clf = div.clf
    data_ = learn_predict_pools(tuple(key for key in POSITIONS), pd.Timestamp(DATE), freq=Freq.quarterly, lags=1)
    clf.fit(data_.x, data_.y)
    print(clf.feature_importances_[:len(POSITIONS)])
    print(clf.feature_importances_[len(POSITIONS):])
    print(div.mean)
