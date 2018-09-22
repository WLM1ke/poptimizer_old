"""Генератор примеров для обучения и предсказания ожидаемой доходности"""
import catboost
import numpy as np
import pandas as pd
from pandas.tseries import offsets

from local import moex, dividends
from utils import aggregation

T2 = 1


class ReturnsCasesIterator:
    def __init__(self, tickers: tuple, last_date: pd.Timestamp, ew_lags: float, lags: int):
        """Генератор кейсов для обучения

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
        lags
            Количество лагов нормированной по СКО доходности, включаемой в кейсы
        """
        self._tickers = tickers
        self._last_date = last_date
        self._ew_lags = ew_lags
        self._lags = lags
        self._returns = self._make_returns()
        self._ew_std = self._returns.ewm(alpha=1 / ew_lags, min_periods=ew_lags).std()

    def _make_returns(self):
        """Создает доходности с учетом дивидендов"""
        prices = moex.prices_t2(self._tickers).fillna(method='ffill', axis='index')
        monthly_prices = prices.groupby(by=aggregation.monthly_aggregation_func(self._last_date)).last()
        monthly_prices = monthly_prices.loc[:self._last_date]

        def t2_shift(x):
            """Рассчитывает T-2 дату

            Если дата не содержится индексе цен, то необходимо найти предыдущую из индекса цен. После этого взять
            сдвинутую на 1 назад дату. Если дата находится в будущем за пределом истории котировок, то достаточно
            сдвинуть на 1 бизнес дня назад - упрощенный подход, который может не корректно работать из-за праздников
            """
            if x <= prices.index[-1]:
                index = prices.index.get_loc(x, 'ffill')
                return prices.index[index - T2]
            return x - T2 * offsets.BDay()

        div = dividends.dividends(self._tickers).loc[monthly_prices.index[0]:, :]
        div.index = div.index.map(t2_shift)
        monthly_dividends = div.groupby(by=aggregation.monthly_aggregation_func(self._last_date)).sum()
        # В некоторые месяцы не платятся дивиденды - без этого буду NaN при расчете доходностей
        monthly_dividends = monthly_dividends.reindex(index=monthly_prices.index, fill_value=0)
        returns = (monthly_prices + monthly_dividends) / monthly_prices.shift(1) - 1
        return returns

    def __iter__(self):
        for date in self._returns.index[self._lags:]:
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
        std = self._ew_std.iloc[first_index + lags - 1, :]
        cases = cases.div(std, axis=1)
        cases = cases.T
        cases.insert(0, 'std', std.T)
        cases.dropna(inplace=True)
        if not labels:
            cases['y'] = np.nan
        cases.columns = ['std'] + [f'lag - {i}' for i in range(self._lags, 0, -1)] + ['y']
        return cases.reset_index()


def learn_pool(tickers: tuple, last_date: pd.Timestamp, ew_lags: float, lags: int):
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
    lags
        Количество лагов нормированной по СКО доходности, включаемой в кейсы

    Returns
    -------
    catboost.Pool
        Кейсы для обучения
    """
    learn_cases = pd.concat(ReturnsCasesIterator(tickers, last_date, ew_lags, lags))
    learn = catboost.Pool(data=learn_cases.iloc[:, :-1],
                          label=learn_cases.iloc[:, -1],
                          cat_features=[0],
                          feature_names=learn_cases.columns[:-1])
    return learn


def predict_pool(tickers: tuple, last_date: pd.Timestamp, ew_lags: float, lags: int):
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
    lags
        Количество лагов нормированной по СКО доходности, включаемой в кейсы

    Returns
    -------
    catboost.Pool
        Кейсы для предсказания
    """
    predict_cases = ReturnsCasesIterator(tickers, last_date, ew_lags, lags).cases(last_date, labels=False)
    print(predict_cases)
    predict = catboost.Pool(data=predict_cases.iloc[:, :-1],
                            label=None,
                            cat_features=[0],
                            feature_names=predict_cases.columns[:-1])
    return predict


if __name__ == '__main__':
    from trading import POSITIONS, DATE

    # 9 7 126 1.00 4.16%

    best = 0
    for lags_std in range(9, 10):
        for lags in range(7, 8):
            print(lags_std, lags, end=' ')
            pool = learn_pool(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), lags_std, lags)
            ignored_features = []
            scores = catboost.cv(
                pool=pool,
                params=dict(
                    random_state=284704,
                    od_type='Iter',
                    verbose=False,
                    allow_writing_files=False,
                    ignored_features=ignored_features),
                fold_count=20)
            index_ = scores['test-RMSE-mean'].idxmin()
            score = scores.loc[index_, 'test-RMSE-mean']
            r2 = 1 - score ** 2 / pd.Series(pool.get_label()).std() ** 2
            if r2 > best:
                best = r2
                print(index_ + 1, f'{score:0.2f}', f'{r2:0.2%}')
            else:
                print(f'{r2:0.2%}')

    pool = learn_pool(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), 9, 7)
    clf = catboost.CatBoostRegressor(
        **dict(
            random_state=284704,
            od_type='Iter',
            verbose=False,
            allow_writing_files=False,
            ignored_features=[],
            iterations=126
        ))
    clf.fit(pool)
    print(clf.feature_importances_)
