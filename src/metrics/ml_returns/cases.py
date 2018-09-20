"""Генератор примеров для обучения и предсказания ожидаемой доходности"""
import catboost
import collections
import pandas as pd
from pandas.tseries.offsets import BDay

from local import moex, dividends
from web import labels

T2 = 1
DAYS_IN_YEAR = 365.25


class ReturnsCasesIterator:
    def __init__(self, tickers: tuple, last_date: pd.Timestamp, lags: int, u_bound: float, l_bound: float):
        """Формирует обучающие примеры для набора тикеров

        Осуществляется расчет доходностей с учетом дивидендов. Полученные ряды доходностей трансформируются в
        неравномерную временную шкалу: отсечки по шкале происходят, когда накопленная доходность превышает u_bound или
        оказывается меньше l_bound - в результате получается ряд доходностей чуть больше u_bound или чуть меньше
        l_bound (более стационарные и гомоскедастичный).

        Для полученного ряда формируются обучающие примеры из тикера, нескольких лагов доходности и длины временных
        интервалов для этих доходностей

        Parameters
        ----------
        tickers
            Набор тикеров, для которых строятся обучающие примеры
        last_date
            Последняя дата, статистика до которой используется для построения примеров
        lags
            Количество лагов доходности и длины периодов, которые используются в обучающих примерах
        u_bound
            Верхняя граница накопленной доходности, которая используется для отсечки периодов
        l_bound
            Нижняя граница накопленной доходности, которая используется для отсечки периодов
        """
        self._tickers = tickers
        self._last_date = last_date
        self._lags = lags
        self._u_bound = u_bound
        self._l_bound = l_bound
        self._returns = self._make_returns()

    def _make_returns(self):
        """Создает доходности с учетом дивидендов

        Используются котировки в режиме T+2 и учитывается сдвиг относительно даты закрытия реестра
        """
        prices = moex.prices_t2(self._tickers).fillna(method='ffill', axis='index')

        def t2_shift(x):
            """Рассчитывает дату котировок без дивидендов

            Если дата не содержится индексе цен, то необходимо найти предыдущую из индекса цен. После этого взять
            сдвинутую на 1 назад дату. Если дата находится в будущем за пределом истории котировок, то достаточно
            сдвинуть на 1 бизнес дня назад - упрощенный подход, который может не корректно работать из-за праздников
            """
            if x <= prices.index[-1]:
                index = prices.index.get_loc(x, 'ffill')
                return prices.index[index - T2]
            return x - T2 * BDay()

        div = dividends.dividends(self._tickers).loc[prices.index[0]:, :]
        div.index = div.index.map(t2_shift)
        prices = prices.loc[:self._last_date]
        # Если отсечки приходятся на выходные и соседние с ними дни, то последний торговый день с дивидендами задвоится
        div = div.groupby(by=labels.DATE).sum()
        div = div.reindex(index=prices.index, fill_value=0)
        returns = (prices + div) / prices.shift(1) - 1
        return returns

    def __iter__(self):
        for ticker in self._tickers:
            yield from self.cases(ticker)

    def threshold_returns(self, ticker: str):
        """Формирует квазистационарный ряд доходностей с отсечкой по threshold с неравномерным временем"""
        returns = self._returns[ticker].dropna(axis=0) + 1
        cum_returns = returns.cumprod(axis=0)
        new_index = collections.deque([cum_returns.index[-1]])
        for back_pos in range(2, cum_returns.index.size + 1):
            last_return = cum_returns[new_index[0]] / cum_returns.iloc[-back_pos]
            if abs(last_return - 1) > self._threshold:
                new_index.appendleft(cum_returns.index[-back_pos])
        cum_returns = cum_returns.reindex(new_index)
        threshold_returns = cum_returns.pct_change().to_frame()
        threshold_returns['len'] = threshold_returns.index
        threshold_returns['len'] = threshold_returns['len'].diff()
        threshold_returns.dropna(axis=0, inplace=True)
        threshold_returns['len'] = threshold_returns['len'].apply(lambda x: x.days)
        threshold_returns['years'] = threshold_returns['len'].rolling(self._lags).sum() / DAYS_IN_YEAR / self._lags
        return threshold_returns

    def cases(self, ticker: str):
        threshold_returns = self.threshold_returns(ticker)
        lags = self._lags
        for index in range(lags, len(threshold_returns)):
            cases = threshold_returns.iloc[index - lags: index + 1, [0]]
            cases = cases.T
            cases.columns = [f'lag - {i}' for i in range(self._lags, 0, -1)] + ['y']

            time = threshold_returns.iloc[index - lags: index, [1]]
            time = time.T
            time.columns = [f't{i}' for i in range(self._lags, 0, -1)]
            time.index = [ticker]
            cases = pd.concat([time, cases], axis=1)
            yield cases.reset_index()


def learn_pool(tickers: tuple, last_date: pd.Timestamp, lags: int, threshold: float):
    learn_cases = pd.concat(ReturnsCasesIterator(tickers, last_date, lags, threshold))
    learn = catboost.Pool(data=learn_cases.iloc[:, :-1],
                          label=learn_cases.iloc[:, -1],
                          cat_features=[0],
                          feature_names=learn_cases.columns[:-1])
    return learn


def predict_pool(tickers: tuple, last_date: pd.Timestamp, lags: int, std_lags: int):
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
        Количество месяцев данных по доходностям
    std_lags
        Количество месяцев, по которым нормируется СКО

    Returns
    -------
    catboost.Pool
        Кейсы для предсказания
    """
    predict_cases = ReturnsCasesIterator(tickers, last_date, lags).cases(last_date, predicted=False)
    predict_cases = normalize_cases(predict_cases, lags, std_lags)
    predict = catboost.Pool(data=predict_cases.iloc[:, :-1],
                            label=None,
                            cat_features=[0],
                            feature_names=predict_cases.columns[:-1])
    return predict


if __name__ == '__main__':
    itr = ReturnsCasesIterator(('RTKMP',), pd.Timestamp('2018-07-15'), 5, 0.01, 0.01)
    print(itr._returns)

    """
    from trading import POSITIONS, DATE

    best = 0
    for threshold in range(9, 1, -1):
        threshold = threshold / 100
        for lags in range(1, 9):
            print(f'{threshold:0.2f}', lags, end=' ')
            pool = learn_pool(tuple(sorted(POSITIONS)), pd.Timestamp(DATE), lags, threshold)
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
                print(index_ + 1, f'{score:0.2%}', f'{r2:0.2%}')
            else:
                print(f'{r2:0.2%}')

    # 0.07 5 130 8.83% 6.57%
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
