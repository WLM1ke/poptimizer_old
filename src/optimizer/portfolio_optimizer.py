"""Класс проводит оптимизацию по Парето на основе метрик доходности и дивидендов"""

import pandas as pd

from optimizer.dividends_metrics import DividendsMetrics
from optimizer.portfolio import Portfolio
from optimizer.returns_metrics import ReturnsMetrics
from optimizer.settings import PORTFOLIO, T_SCORE, CASH

# Максимальный объем операций в долях портфеля
MAX_TRADE = 0.01


class PortfolioOptimizer:
    """Принимает портфель и выбирает наиболее оптимальное направление его улучшения

    При выборе направления улучшения выбираются только те, которые обеспечивают улучшение по каждому из критериев:
    нижней границе дивидендов и величине просадки

    Дополнительно производится оценка возможности значимо (на T_SCORE СКО) минимальную величину дивидендов -
    используется не точный расчет, а линейное приближение
    """

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._dividends = DividendsMetrics(portfolio)
        self._returns = ReturnsMetrics(portfolio)

    def __str__(self):
        t_growth = self.t_growth
        if t_growth > T_SCORE:
            need_optimization = (f'\n\nОПТИМИЗАЦИЯ ТРЕБУЕТСЯ\n\n'
                                 f'Прирост дивидендов составляет {t_growth:.2f} СКО > {T_SCORE:.2f}')
        else:
            need_optimization = (f'\n\nОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ\n\n'
                                 f'Прирост дивидендов составляет {t_growth:.2f} СКО < {T_SCORE:.2f}')

        frames = [self.dividends.gradient,
                  self.returns.gradient,
                  self.dominated,
                  self.gradient_growth]
        columns = ['D_GRADIENT', 'R_GRADIENT', 'DOMINATED', 'GRADIENT_GROWTH']
        df = pd.concat(frames, axis=1)
        df.columns = columns
        df.sort_values('D_GRADIENT', ascending=False, inplace=True)

        return (f'{need_optimization}\n\nКлючевые метрики оптимальности по Парето'
                f'\n\n{df}\n\n{self.best_trade}')

    @property
    def portfolio(self):
        """Оптимизируемый портфель"""
        return self._portfolio

    @property
    def dividends(self):
        """Метрики дивидендов, оптимизируемого портфеля"""
        return self._dividends

    @property
    def returns(self):
        """Метрики доходности, оптимизируемого портфеля"""
        return self._returns

    def _yield_dominated(self):
        """Для каждой позиции выдает доминирующую ее по Парето

        Если доминирующих несколько, то выбирается позиция с максимальным градиентом
        Позиции с нулевым весом не учитываются, так как их нельзя продать
        """
        dividends_gradient = self.dividends.gradient
        returns_gradient = self.returns.gradient
        index = self.portfolio.index
        weight = self.portfolio.weight
        non_zero_positions = index[weight.nonzero()]
        for position in non_zero_positions:
            greater_dividend_gradient = dividends_gradient > dividends_gradient[position]
            greater_return_gradient = returns_gradient > returns_gradient[position]
            pareto_dominance = index[greater_dividend_gradient & greater_return_gradient]
            if not pareto_dominance.empty:
                yield position, dividends_gradient[pareto_dominance].idxmax()

    @property
    def dominated(self):
        """Для каждой позиции выдает доминирующую ее по Парето

        Если доминирующих несколько, то выбирается позиция с максимальным градиентом
        Позиции с нулевым весом не учитываются, так как их нельзя продать"""
        df = pd.Series("", index=self.portfolio.index)
        for position, dominated in self._yield_dominated():
            df[position] = dominated
        return df

    @property
    def gradient_growth(self):
        """Для каждой позиции выдает прирост градиента при покупке доминирующей

        Для позиций не имеющих доминирующих - прирост 0
        """
        df = pd.Series(0.0, index=self.portfolio.index)
        dividends_gradient = self.dividends.gradient
        for position, dominated in self._yield_dominated():
            df[position] = dividends_gradient[dominated] - dividends_gradient[position]
        return df

    @property
    def t_growth(self):
        """Приблизительная оценка потенциального улучшения дивидендов

        Линейное приближение - доля позиций умножается на градиент роста дивидендов. Результат нормируется на СКО
        дивидендов портфеля для удобства сравнения с критическим уровнем t-статистик
        """
        weighted_growth = (self.portfolio.weight * self.gradient_growth).sum()
        return weighted_growth / self.dividends.std[PORTFOLIO]

    @property
    def best_trade(self):
        """Возвращает строчку с рекомендацией по сделкам

        Лучшая позиция на продажу сокращается до нуля, но не более чем на MAX_TRADE от объема портфеля
        Продажа бьется на 5 сделок с округлением в большую сторону

        Лучшая покупка осуществляется на объем доступного кэша и разбивается на 5 лотов
        """
        portfolio = self.portfolio
        best_sell = self.gradient_growth.idxmax()
        sell_share = min(portfolio.weight[best_sell], MAX_TRADE)
        sell_value = sell_share * portfolio.value[PORTFOLIO]
        sell_5_lots = int(sell_value / portfolio.lot_size[best_sell] / portfolio.price[best_sell] / 5 + 0.5)
        best_buy = self.dominated[best_sell]
        buy_5_lots = int(portfolio.value[CASH] / portfolio.lot_size[best_buy] / portfolio.price[best_buy] / 5)
        return (f'РЕКОМЕНДУЕТСЯ:\n'
                f'Продать {best_sell} - 5 сделок по {sell_5_lots} лотов\n'
                f'Купить {best_buy} - 5 сделок по {buy_5_lots} лотов')


if __name__ == '__main__':
    pos = dict(RTKMP=1475 + 312 + 39,
               MSTT=4650,
               UPRO=1267,
               AKRN=795,
               VSMO=133 + 12,
               GMKN=166 + 57,
               MTSS=749,
               MVID=264 + 62,
               PRTK=101 + 0 + 18,
               LSNGP=81,
               ENRU=319 + 148,
               # PMSBP=450+232,
               MSRS=699,
               LSRG=561 + 0 + 80,
               CHMF=15 + 0 + 40,
               LKOH=123,
               RSTIP=238 + 27,
               MFON=55,
               MRSB=23,
               MRKC=343,
               SNGSP=31,
               AFLT=5,
               KBTK=9)
    port = Portfolio(date='2018-04-04',
                     cash=0 + 2749.64 + 4330.3,
                     positions=pos)
    optimizer = PortfolioOptimizer(port)
    print(optimizer)
