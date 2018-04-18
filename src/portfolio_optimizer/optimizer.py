"""Класс проводит оптимизацию по Парето на основе метрик доходности и дивидендов"""

from functools import lru_cache

import pandas as pd

from portfolio_optimizer import local
from portfolio_optimizer.dividends_metrics import DividendsMetrics
from portfolio_optimizer.portfolio import Portfolio
from portfolio_optimizer.returns_metrics import ReturnsMetrics
from portfolio_optimizer.settings import PORTFOLIO, T_SCORE, CASH

# Максимальный объем операций в долях портфеля
MAX_TRADE = 0.01
# Минимальный оборот акции в процентах от размера портфеля - обнуляются улучшения градиентов
VOLUME_CUT_OFF = 0.0046


class Optimizer:
    """Принимает портфель и выбирает наиболее оптимальное направление его улучшения

    При выборе направления улучшения выбираются только те, которые обеспечивают улучшение по каждому из критериев:
    нижней границе дивидендов и величине просадки. На преимущества акций с маленьким оборотом накладывается понижающий
    коэффициент

    Дополнительно производится оценка возможности значимо увеличить (на T_SCORE СКО) минимальную величину дивидендов -
    используется не точный расчет, а линейное приближение
    """

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._dividends_metrics = DividendsMetrics(portfolio)
        self._returns_metrics = ReturnsMetrics(portfolio)

    def __str__(self):
        draw_down = self._returns_metrics.draw_down[PORTFOLIO]
        expected_dividends = self._dividends_metrics.expected_dividends
        minimal_dividends = self._dividends_metrics.minimal_dividends
        main_metrics = (f'КЛЮЧЕВЫЕ МЕТРИКИ ПОРТФЕЛЯ'
                        f'\nМаксимальная ожидаемая просадка - {draw_down:.4f}'
                        f'\nОжидаемые дивиденды - {expected_dividends:.0f}'
                        f'\nМинимальные дивиденды - {minimal_dividends:.0f}')

        t_growth = self.t_growth
        if t_growth > T_SCORE:
            need_optimization = (f'ОПТИМИЗАЦИЯ ТРЕБУЕТСЯ'
                                 f'\nПрирост дивидендов составляет {t_growth:.2f} СКО > {T_SCORE:.2f}')
        else:
            need_optimization = (f'ОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ'
                                 f'\nПрирост дивидендов составляет {t_growth:.2f} СКО < {T_SCORE:.2f}')

        frames = [self.dividends_metrics.gradient,
                  self.returns_metrics.gradient,
                  self.dominated,
                  self.volume_factor,
                  self.gradient_growth]
        pareto_metrics = pd.concat(frames, axis=1)
        pareto_metrics.columns = ['D_GRADIENT', 'R_GRADIENT', 'DOMINATED', 'VOLUME_FACTOR', 'GRADIENT_GROWTH']
        pareto_metrics.sort_values('D_GRADIENT', ascending=False, inplace=True)

        return (f'\n{main_metrics}'
                f'\n'
                f'\n{need_optimization}'
                f'\n'
                f'\n{self.best_trade}'
                f'\n'
                f'\nКЛЮЧЕВЫЕ МЕТРИКИ ОПТИМАЛЬНОСТИ ПО ПАРЕТО'
                f'\n'
                f'\n{pareto_metrics}')

    @property
    def portfolio(self):
        """Оптимизируемый портфель"""
        return self._portfolio

    @property
    def dividends_metrics(self):
        """Метрики дивидендов, оптимизируемого портфеля"""
        return self._dividends_metrics

    @property
    def returns_metrics(self):
        """Метрики доходности, оптимизируемого портфеля"""
        return self._returns_metrics

    @property
    @lru_cache(maxsize=1)
    def volume_factor(self):
        """Понижающий коэффициент для акций с малым объемом оборотов

        Ликвидность в первом приближении убывает пропорционально квадрату оборота, что отражено в формулах расчета
        """
        portfolio = self.portfolio
        last_volume = local.volumes(portfolio.positions[:-2]).loc[portfolio.date]
        volume_share_of_portfolio = last_volume * portfolio.price[:-2] / portfolio.value[PORTFOLIO]
        volume_factor = 1 - (VOLUME_CUT_OFF / volume_share_of_portfolio) ** 2
        volume_factor[volume_factor < 0] = 0
        return volume_factor.reindex(index=portfolio.positions, fill_value=1)

    def _yield_dominated(self):
        """Для каждой позиции выдает доминирующую ее по Парето

        Если доминирующих несколько, то выбирается позиция с максимальным градиентом
        Позиции с нулевым весом не учитываются, так как их нельзя продать
        """
        dividends_gradient = self.dividends_metrics.gradient
        returns_gradient = self.returns_metrics.gradient
        index = pd.Index(self.portfolio.positions)
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
    @lru_cache(maxsize=1)
    def dominated(self):
        """Для каждой позиции выдает доминирующую ее по Парето

        Если доминирующих несколько, то выбирается позиция с максимальным ростом градиента
        Учитывается понижающий коэффициент для низколиквидных доминирующих акций
        """
        df = pd.Series("", index=self.portfolio.positions)
        for position, dominated in self._yield_dominated():
            df[position] = dominated
        return df

    @property
    @lru_cache(maxsize=1)
    def gradient_growth(self):
        """Для каждой позиции выдает прирост градиента при покупке доминирующей

        Для позиций не имеющих доминирующих - прирост 0
        Учитывается понижающий коэффициент для низколиквидных доминирующих акций
        """
        dividends_gradient = self.dividends_metrics.gradient
        factor = self.volume_factor
        df = (dividends_gradient[self.dominated].values - dividends_gradient) * factor[self.dominated].values
        return df.fillna(0)

    @property
    def t_growth(self):
        """Приблизительная оценка потенциального улучшения дивидендов

        Линейное приближение - доля позиций умножается на градиент роста дивидендов. Результат нормируется на СКО
        дивидендов портфеля для удобства сравнения с критическим уровнем t-статистик
        """
        weighted_growth = (self.portfolio.weight * self.gradient_growth).sum()
        return weighted_growth / self.dividends_metrics.std[PORTFOLIO]

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
        sell_weight = min(portfolio.weight[best_sell], MAX_TRADE)
        sell_value = sell_weight * portfolio.value[PORTFOLIO]
        sell_5_lots = int(round(sell_value / portfolio.lot_size[best_sell] / portfolio.price[best_sell] / 5 + 0.5))
        best_buy = self.dominated[best_sell]
        buy_5_lots = int(portfolio.value[CASH] / portfolio.lot_size[best_buy] / portfolio.price[best_buy] / 5)
        return (f'РЕКОМЕНДУЕТСЯ'
                f'\nПродать {best_sell} - 5 сделок по {sell_5_lots} лотов'
                f'\nКупить {best_buy} - 5 сделок по {buy_5_lots} лотов')


if __name__ == '__main__':
    pos = dict(MFON=55,
               LSNGP=81,
               MTSS=749,
               AKRN=795,
               MSRS=699,
               UPRO=1267,
               MRSB=23,
               LKOH=123)
    port = Portfolio(date='2018-04-06',
                     cash=4330.3,
                     positions=pos)
    optimizer = Optimizer(port)
    print(optimizer)
