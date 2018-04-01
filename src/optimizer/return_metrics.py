"""Реализация основных метрик доходности"""

import pandas as pd

from optimizer.portfolio import Portfolio
from optimizer.settings import PORTFOLIO


class ReturnMetrics:
    """Метрики доходности расчитываются на дату формирования портфеля для месячных таймфреймов"""

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._tickers = portfolio.index[:-2]

    def __str__(self):
        pass

    @property
    def monthly_prices(self):
        """Формирует DataFrame цен с шагом в месяц

        Эти ряды цен служат для расчета всех дальнейших показателей
        """
        prices = self._portfolio.prices
        date_tuple = self._portfolio.date.timetuple()[:3]
        reversed_index = []
        for date in reversed(prices.index):
            if date_tuple < date.timetuple()[:3]:
                continue
            else:
                reversed_index.append(date)
                if date_tuple[1] != 1:
                    date_tuple = date_tuple[0], date_tuple[1] - 1, date_tuple[2]
                else:
                    date_tuple = date_tuple[0] - 1, 12, date_tuple[2]
        return prices.loc[reversed(reversed_index)]

    @property
    def returns(self):
        """Доходности составляющих портфеля и самого портфеля

        Доходность кэша - ноль
        Доходность портфеля рассчитывается на основе долей на отчетную дату портфеля
        """
        returns = self.monthly_prices.pct_change()
        returns = returns.reindex(columns=self._portfolio.index)
        returns = returns.fillna(0)
        weight = self._portfolio.weight[self._tickers].transpose()
        returns[PORTFOLIO] = returns[self._tickers].multiply(weight).sum(axis=1)
        return returns

    @property
    def decay(self):
        return 0.92

    @property
    def _weighting(self):
        weights = pd.Series(1 / self.decay, index=self.returns.index)
        weights = weights.cumprod()
        return weights / weights.sum()

    @property
    def mean(self):
        return self.returns.multiply(self._weighting, axis='index').sum(axis='index')


if __name__ == '__main__':
    positions = dict(MSTT=8650,
                     RTKMP=1826,
                     UPRO=3370,
                     LKOH=2230,
                     MVID=3260)
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=positions)
    metrics = ReturnMetrics(port)
    print(metrics.mean)
