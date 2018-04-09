"""Класс проводит оптимизацию по Парето на основе метрик доходности и дивидендов"""

import pandas as pd

from portfolio_optimizer import getter
from portfolio_optimizer.dividends_metrics import DividendsMetrics
from portfolio_optimizer.portfolio import Portfolio
from portfolio_optimizer.returns_metrics import ReturnsMetrics
from portfolio_optimizer.settings import PORTFOLIO, T_SCORE, CASH

# Максимальный объем операций в долях портфеля
MAX_TRADE = 0.01
# Оборот, при котором обнуляются градиенты, в процентах от размера портфеля
VOLUME_CUT_OFF = 0.0024


class Optimizer:
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
                  self.volume_factor,
                  self.gradient_growth]
        columns = ['D_GRADIENT', 'R_GRADIENT', 'DOMINATED', 'VOLUME_FACTOR', 'GRADIENT_GROWTH']
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

    @property
    def volume_factor(self):
        """Понижающий коэффициент для акций с малым объемом оборотов

        Ликвидность в первом приближении убывает пропорционально квадрату оборота, что отражено в формулах расчета
        """
        portfolio = self.portfolio
        tickers = portfolio.tickers
        last_volume = getter.volumes_history(tickers).loc[portfolio.date]
        volume_share_of_portfolio = last_volume * portfolio.price[tickers] / portfolio.value[PORTFOLIO]
        volume_factor = 1 - (VOLUME_CUT_OFF / volume_share_of_portfolio) ** 2
        volume_factor[volume_factor < 0] = 0
        return volume_factor.reindex(index=portfolio.index, fill_value=1)

    def _yield_dominated(self):
        """Для каждой позиции выдает доминирующую ее по Парето

        Если доминирующих несколько, то выбирается позиция с максимальным градиентом
        Позиции с нулевым весом не учитываются, так как их нельзя продать
        """
        dividends_gradient = self.dividends.gradient
        returns_gradient = self.returns.gradient
        index = self.portfolio.index
        weight = self.portfolio.weight
        non_zero_positions = index[weight > 0]
        volume_factor = self.volume_factor
        non_zero_factor = volume_factor > 0
        for position in non_zero_positions:
            greater_dividend_gradient = dividends_gradient > dividends_gradient[position]
            greater_return_gradient = returns_gradient > returns_gradient[position]
            pareto_dominance = index[greater_dividend_gradient & greater_return_gradient & non_zero_factor]
            if not pareto_dominance.empty:
                factor_gradient = (dividends_gradient - dividends_gradient[position]) * volume_factor
                yield position, factor_gradient[pareto_dominance].idxmax()

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
        Учитывается понижающий коэффициент для низколиквидных доминирующих акций
        """
        df = pd.Series(0.0, index=self.portfolio.index)
        dividends_gradient = self.dividends.gradient
        factor = self.volume_factor
        for position, dominated in self._yield_dominated():
            df[position] = (dividends_gradient[dominated] - dividends_gradient[position]) * factor[dominated]
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
        # Отбрасывается портфель и кэш из рекомендаций
        best_sell = self.gradient_growth.iloc[:-2].idxmax()
        sell_share = min(portfolio.weight[best_sell], MAX_TRADE)
        sell_value = sell_share * portfolio.value[PORTFOLIO]
        sell_5_lots = int(sell_value / portfolio.lot_size[best_sell] / portfolio.price[best_sell] / 5 + 1.0)
        best_buy = self.dominated[best_sell]
        buy_5_lots = int(portfolio.value[CASH] / portfolio.lot_size[best_buy] / portfolio.price[best_buy] / 5)
        return (f'РЕКОМЕНДУЕТСЯ:\n'
                f'Продать {best_sell} - 5 сделок по {sell_5_lots} лотов\n'
                f'Купить {best_buy} - 5 сделок по {buy_5_lots} лотов')


if __name__ == '__main__':
    """pr = cProfile.Profile()
    pr.enable()"""

    pos = dict(BANEP=0,
               MFON=55,
               SNGSP=31,
               RTKM=0,
               MAGN=0,
               MSTT=4650,
               KBTK=9,
               MOEX=0,
               RTKMP=1826,
               NMTP=0,
               TTLK=0,
               LSRG=641,
               LSNGP=81,
               PRTK=119,
               MTSS=749,
               AKRN=795,
               MRKC=343,
               GAZP=0,
               AFLT=5,
               MSRS=699,
               UPRO=1267,
               PMSBP=682,
               CHMF=55,
               GMKN=223,
               VSMO=145,
               RSTIP=265,
               PHOR=0,
               MRSB=23,
               LKOH=123,
               ENRU=467,
               MVID=326)
    port = Portfolio(date='2018-03-19',
                     cash=0 + 2749.64 + 4330.3,
                     positions=pos)
    optimizer = Optimizer(port)
    print(optimizer)

    """pr.disable()
    ps = pstats.Stats(pr).sort_stats('cumulative')
    ps.print_stats()"""
