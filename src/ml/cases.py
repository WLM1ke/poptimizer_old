"""Генерация кейсов для обучения и валидации моделей"""
import pandas as pd

import local
from local.local_dividends import STATISTICS_START
from settings import AFTER_TAX
from utils.aggregation import yearly_aggregation_func
from utils.data_manager import AbstractDataManager
from web.labels import TICKER, DATE

CASES_NAME = 'cases'

MONTH_IN_YEAR = 12


class CasesIterator:
    """Итератор кейсов для обучения"""

    def __init__(self, tickers: tuple, last_date: pd.Timestamp, lags: int = 5):
        self._tickers = tickers
        self._last_date = last_date
        self._lags = lags

    def __iter__(self):
        start_date = pd.Timestamp(STATISTICS_START) + pd.DateOffset(years=self._lags + 1)
        index = local.prices(self._tickers).index
        for date in index:
            if start_date <= date <= self._last_date:
                yield self.cases(date)

    def _real_dividends_yields(self, date: pd.Timestamp):
        """Возвращает годовые посленалоговые дивидендные доходности в постоянных ценах для заданной даты

        Информация за lags + 1 лет, базисом для постоянных цен и доходности является предпоследний год
        """
        tickers = self._tickers
        months = MONTH_IN_YEAR * (self._lags + 1)
        cum_cpi = local.monthly_cpi(date).iloc[-months:].cumprod()
        cpi_index = cum_cpi.iat[-MONTH_IN_YEAR - 1] / cum_cpi
        dividends = local.monthly_dividends(tickers, date).iloc[-months:, :]
        after_tax_dividends = dividends * AFTER_TAX
        real_after_tax_dividends = after_tax_dividends.mul(cpi_index, axis='index')
        yearly_dividends = real_after_tax_dividends.groupby(by=yearly_aggregation_func(end_of_year=date)).sum()
        prices = local.prices(tickers)
        price = prices.reindex(cum_cpi.index[-MONTH_IN_YEAR - 1:-MONTH_IN_YEAR], method='ffill').iloc[0]
        return yearly_dividends.div(price.values, axis='columns')

    def cases(self, date: pd.Timestamp):
        """Возвращает кейсы для заданной даты"""
        dividends_yield = self._real_dividends_yields(date)
        date = dividends_yield.index[-2]
        dividends_yield = dividends_yield.T
        dividends_yield.index.name = TICKER
        dividends_yield[DATE] = date
        dividends_yield.set_index(DATE, append=True, inplace=True)
        dividends_yield.columns = (f'lag - {i}' for i in range(self._lags, -1, -1))
        return dividends_yield.dropna()


class CasesDataManager(AbstractDataManager):
    """Сохраняет кейсы и обновляет раз в день с нуля"""
    update_from_scratch = True
    is_monotonic = False

    def __init__(self, tickers: tuple, last_date: pd.Timestamp, lags: int = 5):
        self._params = (tickers, last_date, lags)
        super().__init__(None, CASES_NAME)
        if self.value.shape[1] != lags + 1:
            raise ValueError(f'Локальная версия для {self.value.shape[1] - 1} лагов'
                             f'\nДолжна быть для {lags}')
        if self.value.index[-1][1] != last_date + pd.DateOffset(years=-1):
            raise ValueError(f'Локальная версия для {self.value.index[-1][1]} даты'
                             f'\nДолжна быть для {last_date + pd.DateOffset(years=-1)}')
        if set(tickers) != set(self.value.index.levels[0]):
            raise ValueError(f'Локальная версия для {sorted(set(tickers))} тикеров'
                             f'\nДолжна быть для {sorted(set(self.value.index.levels[0]))}')

    def download_all(self):
        return pd.concat(CasesIterator(*self._params))

    def download_update(self):
        super().download_update()


def all_cases(tickers: tuple, last_date: pd.Timestamp, lags: int = 5):
    """Возвращает обучающую выборку до указанной даты включительно

    Для каждого тикера и Timestamp начала нулевого периода значение реальной годовой дивидендной доходности с
    несколькими лагами. Дивидендная доходность пересчитывается в постоянные цены на начало нулевого периода

    Parameters
    ----------
    tickers
        Кортеж тикеров
    last_date
        Последняя дата, на которую нужно подготовить кейсы
    lags
        Количество лагов для данных по дивидендам

    Returns
    -------
    DataFrame
        Мультииндекс - тикер, дата нулевого периода
        Столбцы - лаговые значения дивидендов, а в последнем столбце значение без лага
    """
    return CasesDataManager(tickers, last_date, lags).value

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
                     ALRS=0)

    manager = CasesDataManager(tuple(key for key in POSITIONS), pd.Timestamp('2018-08-13'))
    print(manager.value)
