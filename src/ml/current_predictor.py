"""Реализация текущего предсказания в формате sklearn"""
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.metrics import r2_score


class AverageRegressor(BaseEstimator, RegressorMixin):
    def __init__(self):
        pass

    def get_params(self, deep=True):
        return {}

    def set_params(self, **params):
        pass

    def fit(self, x, y, sample_weight=None):
        return self

    @staticmethod
    def predict(x):
        return x.values.mean(axis=1)

    def score(self, x, y, sample_weight=None):
        return r2_score(y, self.predict(x), sample_weight)


if __name__ == '__main__':
    pass
