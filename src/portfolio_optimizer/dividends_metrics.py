"""Реализация основных метрик дивидендного потока"""

import pandas as pd

from portfolio_optimizer import local
from portfolio_optimizer.portfolio import Portfolio
from portfolio_optimizer.settings import PORTFOLIO, AFTER_TAX, T_SCORE, CASH


class DividendsMetrics:
    """Реализует основные метрики дивидендного потока для портфеля

    За основу берутся legacy dividends, которые переводятся в
    реальные посленалоговые величины и используются для расчета разнообразных метрик
    """

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._index = portfolio.index

    def __str__(self):
        expected_dividends = self.mean[PORTFOLIO] * self._portfolio.value[PORTFOLIO]
        minimal_dividends = self.lower_bound[PORTFOLIO] * self._portfolio.value[PORTFOLIO]
        frames = [self.mean,
                  self.std,
                  self.beta,
                  self.lower_bound,
                  self.gradient]
        columns = ['MEAN', 'STD', 'BETA', 'LOWER_BOUND', 'GRADIENT']
        df = pd.concat(frames, axis=1)
        df.columns = columns
        return (f'\nКЛЮЧЕВЫЕ МЕТРИКИ ДИВИДЕНДОВ:\n\n'
                f'Ожидаемые дивиденды - {expected_dividends:.0f}\n'
                f'Минимальные дивиденды дивиденды - {minimal_dividends:.0f}\n\n'
                f'{df}')

    @property
    def nominal_pretax(self):
        """Дивиденды в номинальном выражении"""
        index = self._index
        tickers = index[:-2]
        df = local.legacy_dividends(tickers).transpose()
        df.reindex(index=index)
        df.loc[CASH] = 0
        amount = self._portfolio.shares
        df.loc[PORTFOLIO] = df.multiply(amount, axis='index').sum(axis=0)
        return df

    @property
    def real_after_tax(self):
        """Дивиденды после уплаты налогов в реальном выражении (в ценах последнего года)

        Все метрики опираются именно на реальные посленалоговые выплаты
        1 - ставка налога = AFTER_TAX указывается в модуле настроек
        """
        nominal_pretax_dividends = self.nominal_pretax
        columns = nominal_pretax_dividends.columns
        cum_cpi = local.cpi().cumprod()
        years_end_date = [pd.to_datetime(f'{year}-12-31') for year in columns]
        last_year_cpi_values = (cum_cpi[years_end_date[-1]] / cum_cpi[years_end_date]).values
        real_pretax_dividends = nominal_pretax_dividends.multiply(last_year_cpi_values, axis='columns')
        return real_pretax_dividends * AFTER_TAX

    @property
    def yields(self):
        """Дивидендная доходность"""
        dividends = self.real_after_tax
        inverse_prices = 1 / self._portfolio.price
        return dividends.multiply(inverse_prices, axis='index')

    @property
    def mean(self):
        """Матожидание дивидендной доходности"""
        return self.yields.mean(axis='columns', skipna=False)

    @property
    def std(self):
        """СКО дивидендной доходности

        СКО портфеля рассчитывается из допущения нулевой корреляции между дивидендами отдельных позиций. Допущение о
        нулевой корреляции необходимо в качестве простого приема регуляризации, так как число лет существенно меньше
        количества позиций. Данное допущение используется во всех дальнейших расчетах
        """
        std = self.yields.std(axis='columns', ddof=1, skipna=False)
        tickers = self._index[:-2]
        weighted_std = std.loc[tickers] * self._portfolio.weight[tickers]
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
        return self.mean - T_SCORE * self.std

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


if __name__ == '__main__':
    pos = dict(UPRO=1267,
               LSNGP=81,
               LKOH=123,
               SNGSP=31,
               AFLT=5)
    port = Portfolio(date='2018-04-04',
                     cash=4330.3,
                     positions=pos)
    print(DividendsMetrics(port))
