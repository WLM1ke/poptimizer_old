"""Реализация основных метрик дивидендного потока с помощью ML-модели"""
import pandas as pd

import ml.manager
from metrics.dividends_metrics import AbstractDividendsMetrics
from metrics.portfolio import Portfolio


class MLDividendsMetrics(AbstractDividendsMetrics):
    """Реализует основные метрики дивидендного потока для портфеля с помощью ML-модели

    ML-модели строится с помощью Gradient Boosting по данным с лагом о предыдущей дивидендной доходности и
    категориальной переменной на основе тикеров. СКО прогноза вычисляется с помощью кросс-валидации
    """

    @property
    def _tickers_real_after_tax_mean(self):
        portfolio = self._portfolio
        manager = ml.manager.DividendsMLDataManager(portfolio.positions[:-2], pd.Timestamp(portfolio.date))
        return manager.value.div_prediction

    @property
    def _tickers_real_after_tax_std(self):
        portfolio = self._portfolio
        manager = ml.manager.DividendsMLDataManager(portfolio.positions[:-2], pd.Timestamp(portfolio.date))
        return pd.Series(manager.value.std, index=portfolio.positions[:-2])


if __name__ == '__main__':
    pos = dict(
        AKRN=563,
        BANEP=488 + 19,
        CHMF=234 + 28 + 8,
        GMKN=146 + 29,
        LKOH=290 + 18,
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
        TATNP=0)
    port = Portfolio(date='2018-09-03',
                     cash=236_460 + 3_649 + 3_406,
                     positions=pos)
    print(MLDividendsMetrics(port))
