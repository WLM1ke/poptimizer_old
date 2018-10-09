"""Генератор примеров для обучения и предсказания ожидаемой доходности"""
import catboost
import numpy as np
import pandas as pd

from local import moex


class ReturnsCasesIterator:
    def __init__(self, tickers: tuple, last_date: pd.Timestamp, ew_lags: float, returns_lags: int):
        """Генератор кейсов для обучения

        Обучающие кейсы состоят из тикера, экспоненциально сглаженного СКО и среднего и нескольких последних
        доходностей. Среднее и доходности нормируются на экспоненциальное СКО, а доходности также центрируются по
        экспоненциальному среднему

        Parameters
        ----------
        tickers
            Тикеры, для которых необходимо создать обучающие примеры
        last_date
            Дата, до которой используется статистика
        ew_lags
            1 / ew_lags - константа экспоненциального сглаживания
        returns_lags
            Количество лагов нормированной по СКО доходности, включаемой в кейсы
        """
        self._tickers = tickers
        self._last_date = last_date
        self._ew_lags = ew_lags
        self._lags = returns_lags
        self._returns = moex.log_returns_with_div(tickers, last_date)
        ewm = self._returns.ewm(alpha=1 / ew_lags, min_periods=ew_lags)
        self._ew_mean = ewm.mean()
        self._ew_std = ewm.std()

    def __iter__(self):
        for date in self._returns.index[self._ew_lags:]:
            yield self.cases(date)

    def cases(self, date: pd.Timestamp, labels: bool = True):
        """Кейсы для заданной даты с возможностью отключения меток"""
        lags = self._lags
        returns = self._returns
        last_index = returns.index.get_loc(date)
        first_index = last_index - lags
        if not labels:
            first_index += 1
        cases = returns.iloc[first_index:last_index + 1, :]

        mean = self._ew_mean.iloc[first_index + lags - 1, :]
        cases = cases.sub(mean, axis=1)

        std = self._ew_std.iloc[first_index + lags - 1, :]
        cases = cases.div(std, axis=1)

        cases = cases.T

        mean = mean.div(std)
        cases.insert(0, 'mean', mean.T)

        cases.insert(0, 'std', std.T)
        cases.dropna(inplace=True)

        if not labels:
            cases['y'] = np.nan
        cases.columns = ['std', 'mean'] + [f'lag - {i}' for i in range(self._lags, 0, -1)] + ['y']
        return cases.reset_index()


def learn_pool(tickers: tuple, last_date: pd.Timestamp, ew_lags: float, returns_lags: int):
    """Возвращает обучающие кейсы до указанной даты включительно в формате Pool

    Обучающие кейсы состоят из тикера, экспоненциально сглаженного СКО и нескольких последних доходностей,
    нормированных на СКО

    Parameters
    ----------
    tickers
        Тикеры, для которых необходимо создать обучающие примеры
    last_date
        Дата, до которой используется статистика
    ew_lags
        1 / ew_lags - константа экспоненциального сглаживания
    returns_lags
        Количество лагов нормированной по СКО доходности, включаемой в кейсы

    Returns
    -------
    catboost.Pool
        Кейсы для обучения
    """
    learn_cases = pd.concat(ReturnsCasesIterator(tickers, last_date, ew_lags, returns_lags))
    learn = catboost.Pool(data=learn_cases.iloc[:, :-1],
                          label=learn_cases.iloc[:, -1],
                          cat_features=[0],
                          feature_names=learn_cases.columns[:-1])
    return learn


def predict_pool(tickers: tuple, last_date: pd.Timestamp, ew_lags: float, returns_lags: int):
    """Возвращает кейсы предсказания до указанной даты включительно в формате Pool

    Обучающие кейсы состоят из тикера, экспоненциально сглаженного СКО и нескольких последних доходностей,
    нормированных на СКО

    Parameters
    ----------
    tickers
        Тикеры, для которых необходимо создать обучающие примеры
    last_date
        Дата, до которой используется статистика
    ew_lags
        1 / ew_lags - константа экспоненциального сглаживания
    returns_lags
        Количество лагов нормированной по СКО доходности, включаемой в кейсы

    Returns
    -------
    catboost.Pool
        Кейсы для предсказания
    """
    predict_cases = ReturnsCasesIterator(tickers, last_date, ew_lags, returns_lags).cases(last_date, labels=False)
    predict = catboost.Pool(data=predict_cases.iloc[:, :-1],
                            label=None,
                            cat_features=[0],
                            feature_names=predict_cases.columns[:-1])
    return predict


if __name__ == '__main__':
    # print(pd.concat(ReturnsCasesIterator(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), 7, 0), ignore_index=True))

    ret = moex.log_returns_with_div(('LSNGP', 'MTSS', 'PRTK', 'GMKN', 'AKRN'), pd.Timestamp('2018-10-08'))

    print(ret)
    print(ret.ewm(alpha=1 / 9, min_periods=9).std())
    print(ret.ewm(alpha=1 / 9, min_periods=9).mean())
