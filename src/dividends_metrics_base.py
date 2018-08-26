"""Реализация основных метрик дивидендного потока классической схеме"""

from functools import lru_cache

import local
from dividends_metrics import AbstractDividendsMetrics
from portfolio import Portfolio
from settings import AFTER_TAX
# Период, который является источником для статистики
from utils.aggregation import yearly_aggregation_func

DIVIDENDS_YEARS = 5
DIVIDENDS_MONTHS = DIVIDENDS_YEARS * 12


class BaseDividendsMetrics(AbstractDividendsMetrics):
    """Реализует основные метрики дивидендного потока для портфеля по базовой схеме

    За основу берутся данные из базы данных по дивидендам, которые переводятся в реальные посленалоговые величины
    """

    @property
    def nominal_pretax_monthly(self):
        """Дивиденды в номинальном выражении по месяцам"""
        positions = self._portfolio.positions
        df = local.monthly_dividends(positions[:-2], self._portfolio.date)
        df = df.iloc[-DIVIDENDS_MONTHS:]
        df.reindex(index=positions)
        return df

    @property
    def real_after_tax_monthly(self):
        """Дивиденды после уплаты налогов в реальном выражении по месяцам (в ценах последнего месяца)

        Все метрики опираются именно на реальные посленалоговые выплаты
        1 - ставка налога = AFTER_TAX указывается в модуле настроек
        """
        nominal_pretax_dividends = self.nominal_pretax_monthly
        cpi = local.monthly_cpi(self._portfolio.date)
        cum_cpi = cpi.iloc[-DIVIDENDS_MONTHS:].cumprod()
        real_index = cum_cpi.iloc[-1] / cum_cpi
        real_pretax_dividends = nominal_pretax_dividends.multiply(real_index, axis='index')
        return real_pretax_dividends * AFTER_TAX

    @property
    def real_after_tax(self):
        """Дивиденды после уплаты налогов в реальном выражении по годам (в ценах последнего месяца)

        Все метрики опираются именно на реальные посленалоговые выплаты
        1 - ставка налога = AFTER_TAX указывается в модуле настроек
        """
        real_after_tax = self.real_after_tax_monthly
        return real_after_tax.groupby(by=yearly_aggregation_func(self._portfolio.date)).sum()

    @property
    @lru_cache(maxsize=1)
    def yields(self):
        """Дивидендная доходность"""
        dividends = self.real_after_tax
        inverse_prices = 1 / self._portfolio.price[dividends.columns]
        return dividends.multiply(inverse_prices, axis='columns')

    @property
    def _tickers_real_after_tax_mean(self):
        return self.yields.mean(axis='index', skipna=False)

    @property
    def _tickers_real_after_tax_std(self):
        return self.yields.std(axis='index', ddof=1, skipna=False)


if __name__ == '__main__':
    pos = dict(AKRN=676,
               BANEP=392,
               CHMF=173,
               GMKN=139,
               LKOH=183,
               LSNGP=596,
               LSRG=2346,
               MSRS=128,
               MSTT=1823,
               MTSS=1348,
               MVID=141,
               PMSBP=2715,
               RTKMP=1674,
               SNGSP=263,
               TTLK=234,
               UPRO=1272,
               VSMO=101)
    port = Portfolio(date='2018-07-27',
                     cash=2_482 + 7_764 + 3_416,
                     positions=pos)
    print(BaseDividendsMetrics(port))
