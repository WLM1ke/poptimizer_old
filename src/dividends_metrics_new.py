"""Реализация основных метрик дивидендного потока"""

from functools import lru_cache

import pandas as pd

import local
from local import dividends_update_status
from portfolio import Portfolio, CASH, PORTFOLIO
from settings import AFTER_TAX, T_SCORE

# Период, который является источником для статистики
DIVIDENDS_YEARS = 5
DIVIDENDS_MONTHS = DIVIDENDS_YEARS * 12


class DividendsMetrics:
    """Реализует основные метрики дивидендного потока для портфеля

    За основу берутся legacy dividends_metrics, которые переводятся в реальные посленалоговые величины и используются
    для расчета разнообразных метрик
    """

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio

    def __str__(self):
        frames = [self.mean,
                  self.std,
                  self.beta,
                  self.lower_bound,
                  self.gradient,
                  self.data_status]
        df = pd.concat(frames, axis=1)
        df.columns = ['MEAN', 'STD', 'BETA', 'LOWER_BOUND', 'GRADIENT', 'STATUS']
        return (f'\nКЛЮЧЕВЫЕ МЕТРИКИ ДИВИДЕНДОВ'
                f'\n'
                f'\nОжидаемые дивиденды - {self.expected_dividends:.0f}'
                f'\nМинимальные дивиденды дивиденды - {self.minimal_dividends:.0f}'
                f'\n'
                f'\n{df}')

    @property
    def nominal_pretax_monthly(self):
        """Дивиденды в номинальном выражении по месяцам"""
        positions = self._portfolio.positions
        df = local.monthly_dividends(positions[:-2], self._portfolio.date)
        df = df.iloc[-DIVIDENDS_MONTHS:]
        df.reindex(index=positions)
        df[CASH] = 0
        df[PORTFOLIO] = df.multiply(self._portfolio.shares, axis='columns').sum(axis=1)
        return df

    @property
    def real_after_tax_monthly(self):
        """Дивиденды после уплаты налогов в реальном выражении по месяцам (в ценах последнего месяца)

        Все метрики опираются именно на реальные посленалоговые выплаты
        1 - ставка налога = AFTER_TAX указывается в модуле настроек
        """
        nominal_pretax_dividends = self.nominal_pretax_monthly
        cpi = local.cpi_to_date(self._portfolio.date)
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
        end_month = self._portfolio.date.month

        def yearly_aggregation(x: pd.Timestamp):
            if x.month <= end_month:
                return x + pd.DateOffset(month=end_month)
            else:
                return x + pd.DateOffset(years=1, month=end_month)

        return real_after_tax.groupby(by=yearly_aggregation).sum()

    @property
    @lru_cache(maxsize=1)
    def yields(self):
        """Дивидендная доходность"""
        dividends = self.real_after_tax
        inverse_prices = 1 / self._portfolio.price
        return dividends.multiply(inverse_prices, axis='columns')

    @property
    def mean(self):
        """Матожидание дивидендной доходности"""
        return self.yields.mean(axis='index', skipna=False)

    @property
    def std(self):
        """СКО дивидендной доходности

        СКО портфеля рассчитывается из допущения нулевой корреляции между дивидендами отдельных позиций. Допущение о
        нулевой корреляции необходимо в качестве простого приема регуляризации, так как число лет существенно меньше
        количества позиций. Данное допущение используется во всех дальнейших расчетах
        """
        std = self.yields.std(axis='index', ddof=1, skipna=False)
        tickers = std.index[:-2]
        weighted_std = std[tickers] * self._portfolio.weight[tickers]
        std[PORTFOLIO] = (weighted_std ** 2).sum(axis='index') ** 0.5
        return std

    @property
    def beta(self):
        """Беты дивидендных доходностей

        Традиционно бета равна cov(r,rp) / var(rp), где r и rp - доходность актива и портфеля, соответственно.
        При используемых допущениях можно показать, что бета равна w * var(r) / var(rp), где w - доля актива в портфеле

        При правильной реализации взвешенная по долям бета отдельных позиций равна бете портфеля и равна 1, а бета кэша
        равна 0
        """
        var = self.std ** 2
        return (self._portfolio.weight * var) / (var[PORTFOLIO])

    @property
    def lower_bound(self):
        """Рассчитывает нижнюю границу доверительного интервала для дивидендной доходности

        Используемая t-статистика берется из файла настроек

        Для оптимизированных портфелей, нижняя граница доверительного интервала выше, чем у отдельных позиций
        """
        lower_bound = self.mean - T_SCORE * self.std
        lower_bound[lower_bound < 0] = 0
        return lower_bound

    @property
    def gradient(self):
        """Рассчитывает производную нижней границы по доле актива в портфеле

        В общем случае равна (m - mp) - t * sp * (b - 1), m и mp - доходность актива и портфеля, соответственно,
        t - t-статистика, sp - СКО портфеля, b - бета актива

        Долю актива с максимальным градиентом необходимо наращивать, а с минимальным сокращать. Так как важную роль в
        градиенте играет бета, то во многих случаях выгодно наращивать долю не той бумаги, у которой самая высокая
        нижняя граница, а той у которой достаточно низкая бета при высокой дивидендной доходности

        При правильной реализации взвешенный по долям отдельных позиций градиент равен градиенту по портфелю в целом и
        равен 0
        """
        mean_gradient = self.mean - self.mean[PORTFOLIO]
        risk_gradient = self.std[PORTFOLIO] * (self.beta - 1)
        return mean_gradient - T_SCORE * risk_gradient

    @property
    def expected_dividends(self):
        """Ожидаемые дивиденды по портфелю в рублевом выражении"""
        return self.mean[PORTFOLIO] * self._portfolio.value[PORTFOLIO]

    @property
    def minimal_dividends(self):
        """Ожидаемые дивиденды по портфелю в рублевом выражении по нижней границе доверительного интервала"""
        return self.lower_bound[PORTFOLIO] * self._portfolio.value[PORTFOLIO]

    @property
    def data_status(self):
        """Статус обновления данных по дивидендам"""
        positions = self._portfolio.positions
        status = dividends_update_status(positions[:-2])
        return status.reindex(index=list(positions),
                              fill_value='OK')


if __name__ == '__main__':
    pos = dict(AKRN=679,
               BANEP=644 + 14 + 16,
               CHMF=108 + 26,
               GMKN=139 + 27,
               LKOH=123,
               LSNGP=59 + 6,
               LSRG=172 + 0 + 80,
               MFON=65 + 0 + 5,
               MSTT=2436,
               MTSS=1179 + 25,
               MVID=186,
               PRTK=13,
               RTKMP=1628 + 382 + 99,
               SNGSP=207,
               TTLK=234,
               UPRO=1114,
               VSMO=83 + 5)
    port = Portfolio(date='2018-05-11',
                     cash=311_587 + 584 + 1_457,
                     positions=pos)
    print(DividendsMetrics(port))
