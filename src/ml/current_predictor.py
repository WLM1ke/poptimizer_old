"""Реализация текущего предсказания в формате sklearn"""

from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.metrics import r2_score


class AverageRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, lags=5):
        self._lags = lags

    def get_params(self, deep=True):
        return {'lags': self._lags}

    def set_params(self, **params):
        self._lags = params['lags']

    def fit(self, x, y, sample_weight=None):
        return self

    def predict(self, x):
        return x.values[:, -self._lags:].mean(axis=1)

    def score(self, x, y, sample_weight=None):
        return r2_score(y, self.predict(x), sample_weight)


if __name__ == '__main__':
    pass
