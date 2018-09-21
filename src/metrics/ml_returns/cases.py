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
        self._tickers = tickers
        self._last_date = last_date
        self.ew_lags = ew_lags
        self.lags = lags
        self._returns = self._make_returns()
        ew_returns = self._returns.ewm(alpha=1 / ew_lags, min_periods=ew_lags)
        self._ew_returns = ew_returns.mean()
        self._ew_std = ew_returns.std()

    def _make_returns(self):
        """Создает доходности с учетом дивидендов"""
        prices = moex.prices_t2(self._tickers).fillna(method='ffill', axis='index')
        monthly_prices = prices.groupby(by=aggregation.monthly_aggregation_func(self._last_date)).last()
        monthly_prices = monthly_prices.loc[:self._last_date]

        def t2_shift(x):
            """Рассчитывает T-2 дату

            Если дата не содержится индексе цен, то необходимо найти предыдущую из индекса цен. После этого взять
            сдвинутую на 2 назад дату. Если дата находится в будущем за пределом истории котировок, то достаточно
            сдвинуть на 2 бизнес дня назад - упрощенный подход, который может не корректно работать из-за праздников
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
        for date in self._returns.index[max(12, self._lags, self._lags_std):]:
            yield self.cases(date)

    def cases(self, date: pd.Timestamp, predicted: bool = True):
        last_index = self._returns.index.get_loc(date)
        first_index = last_index - max(12, self._lags, self._lags_std)
        if not predicted:
            first_index += 1
        cases = self._returns.iloc[first_index:last_index + 1, :]
        cases = cases.T
        cases.dropna(inplace=True)
        if not predicted:
            cases['y'] = np.nan
        cases.columns = [f'lag - {i}' for i in range(max(12, self._lags, self._lags_std), 0, -1)] + ['y']
        std = cases.iloc[:, -1 - self._lags_std:-1].std(axis=1, ddof=2)
        cases = cases.div(std, axis=0)
        cases = cases.iloc[:, -1 - self._lags:]
        cases.insert(0, 'std', std)
        return cases.reset_index()


def learn_pool(tickers: tuple, last_date: pd.Timestamp, lags, lags_std):
    """Возвращает обучающие кейсы до указанной даты включительно в формате Pool

    Кейсы состоят из значений доходности с учетом дивидендов за последние lags месяцев, тикера и СКО, которое
    использовалось для нормирования

    Parameters
    ----------
    tickers
        Кортеж тикеров
    last_date
        Последняя дата, на которую нужно подготовить кейсы
    lags
        Количество лет данных по доходностям

    Returns
    -------
    catboost.Pool
        Кейсы для обучения
    """
    learn_cases = pd.concat(ReturnsCasesIterator(tickers, last_date, lags, lags_std))
    learn = catboost.Pool(data=learn_cases.iloc[:, :-1],
                          label=learn_cases.iloc[:, -1],
                          cat_features=[0],
                          feature_names=learn_cases.columns[:-1])
    return learn


def predict_pool(tickers: tuple, last_date: pd.Timestamp, lags):
    """Возвращает кейсы предсказания до указанной даты включительно в формате Pool

    Кейсы состоят из значений доходности с учетом дивидендов за последние lags месяцев, тикера и СКО, которое
    использовалось для нормирования

    Parameters
    ----------
    tickers
        Кортеж тикеров
    last_date
        Последняя дата, на которую нужно подготовить кейсы
    lags
        Количество лет данных по дивидендам

    Returns
    -------
    catboost.Pool
        Кейсы для предсказания
    """
    predict_cases = ReturnsCasesIterator(tickers, last_date, lags).cases(last_date, predicted=False)
    predict = catboost.Pool(data=predict_cases.iloc[:, :-1],
                            label=None,
                            cat_features=[0],
                            feature_names=predict_cases.columns[:-1])
    return predict


if __name__ == '__main__':
    from trading import POSITIONS, DATE

    itr = ReturnsCasesIterator(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), 10, 1)

    """
    best = 0
    for lags_std in range(3, 13):
        for lags in range(1, 4):
            print(lags_std, lags, end=' ')
            pool = learn_pool(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), lags, lags_std)
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
                print(f'{score:0.2f}', f'{r2:0.2%}')

    # 11 12 77 1.17 7.33%
    """

    """
    pool = learn_pool(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), 1, 0.05)
    clf = catboost.CatBoostRegressor(
        **dict(
            random_state=284704,
            od_type='Iter',
            verbose=False,
            allow_writing_files=False,
            ignored_features=[],
            iterations=119
        ))
    clf.fit(pool)
    print(clf.feature_importances_)
  
    pred_pool = predict_pool(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), 11)
    print(pd.Series(clf.predict(pred_pool), index=sorted(POSITIONS)))
    print(pd.Series(clf.predict(pred_pool), index=sorted(POSITIONS)) * np.array(pred_pool.get_features())[:, 1])
    """
