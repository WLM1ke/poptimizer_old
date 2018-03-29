"""Реализация основных метрик дивидендного потока"""

import pandas as pd

from optimizer import getter
from optimizer.portfolio import Portfolio
from optimizer.settings import LOTS, LOT_SIZE, PORTFOLIO, AFTER_TAX, PRICE, WEIGHT, T_STATISTICS


class DividendsMetrics:
    """Реализует основные метрики дивидендного потока для портфеля

    За основу берутся legacy dividends для интервала лет с first_year до last_year включительно, которые переводятся в
    реальные посленалоговые величины и используются для расчета разнообразных метрик
    """

    def __init__(self, portfolio: Portfolio, first_year: int, last_year: int):
        self._portfolio = portfolio
        self._df = portfolio.df
        self._columns = list(range(first_year, last_year + 1))

    def __str__(self):
        frames = [self.mean(),
                  self.std(),
                  self.beta(),
                  self.lower_bound(),
                  self.gradient_of_lower_bound()]
        columns = ['MEAN', 'STD', 'BETA', 'LOWER_BOUND', 'GRADIENT']
        df = pd.concat(frames, axis=1)
        df.columns = columns
        return f'{self._portfolio}\n\nКлючевые метрики дивидендов:\n\n{df}'

    def nominal_pretax(self):
        """Дивиденды в номинальном выражении"""
        index = self._df.index
        df = pd.DataFrame(0.0, index=index, columns=self._columns)
        tickers = index[:-2]
        df.loc[tickers, self._columns] = getter.legacy_dividends(tickers).transpose()
        amount = self._df[[LOT_SIZE, LOTS]].prod(axis=1)
        df.loc[PORTFOLIO, self._columns] = df.multiply(amount, axis='index').sum(axis=0)
        return df

    def real_after_tax(self):
        """Дивиденды после уплаты налогов в реальном выражении (в ценах последнего года)

        Все метрики опираются именно на реальные посленалоговые выплаты
        """
        cum_cpi = getter.cpi().cumprod()
        years = [pd.to_datetime(f'{year}-12-31') for year in self._columns]
        last_year_cpi_values = (cum_cpi[years[-1]] / cum_cpi[years]).values
        nominal_pretax_dividends = self.nominal_pretax()
        real_pretax_dividends = nominal_pretax_dividends.multiply(last_year_cpi_values, axis='columns')
        return real_pretax_dividends * AFTER_TAX

    def yields(self):
        """Дивидендная доходность"""
        dividends = self.real_after_tax()
        inverse_prices = 1 / self._df[PRICE]
        return dividends.multiply(inverse_prices, axis='index')

    def mean(self):
        """Матожидание дивидендной доходности"""
        return self.yields().mean(axis='columns', skipna=False)

    def std(self):
        """СКО дивидендной доходности

        СКО портфеля рассчитывается из допущения нулевой корреляции между дивидендами отдельных позиций. Допущение о
        нулевой корреляции необходимо в качестве простого приема регуляризации, так как число лет существенно меньше
        количества позиций. Данное допущение используется во всех дальнейших расчетах
        """
        std = self.yields().std(axis='columns', ddof=1, skipna=False)
        tickers = self._df.index[:-2]
        weighted_std = std.loc[tickers] * self._df.loc[tickers, WEIGHT]
        std[PORTFOLIO] = (weighted_std ** 2).sum(axis='index') ** 0.5
        return std

    def beta(self):
        """Беты дивидендных доходностей

        Традиционно бета равна cov(r,rp) / var(rp), где r и rp - доходность актива и портфеля, соответственно.
        При используемых допущениях можно показать, что бета равна w * var(r) / var(rp), где w - доля актива в портфеле

        При правильной реализации взвешенная по долям бета отдельных позиций равна бете портфеля и равна 1, а бета кэша
        равна 0
        """
        var = self.std() ** 2
        return (self._df[WEIGHT] * var) / (var[PORTFOLIO])

    def lower_bound(self):
        """Рассчитывает нижнюю границу доверительного интервала для дивидендной доходности

        Используемая t-статистика берется из файла настроек

        Для оптимизированных портфелей, нижняя граница доверительного интервала выше, чем у отдельных позиций
        """
        return self.mean() - T_STATISTICS * self.std()

    def gradient_of_lower_bound(self):
        """Рассчитывает производную нижней границы по доле актива в портфеле

        В общем случае равна (r - rp) - t * sp * (b - 1), r и rp - доходность актива и портфеля, соответственно,
        t - t-статистика, sp - СКО портфеля, b - бета актива

        Долю актива с максимальным градиентом необходимо наращивать, а с минимальным сокращать. Так как важную роль в
        градиенте играет бета, то во многих случаях выгодно наращивать долю не той бумаги, у которой самая высокая
        нижняя граница, а той у которой достаточно низкая бета при высокой дивидендной доходности

        При правильной реализации взвешенный по долям отдельных позиций градиент равен градиенту по портфелю в целом и
        равен 0
        """
        mean_gradient = self.mean() - self.mean()[PORTFOLIO]
        risk_gradient = self.std()[PORTFOLIO] * (self.beta() - 1)
        return mean_gradient - T_STATISTICS * risk_gradient


if __name__ == '__main__':
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123))
    div = DividendsMetrics(port, 2012, 2016)
    print(div)
