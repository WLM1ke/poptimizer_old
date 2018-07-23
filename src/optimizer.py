"""Класс проводит оптимизацию по Парето на основе метрик доходности и дивидендов"""

import pandas as pd

from dividends_metrics import DividendsMetrics
from portfolio import Portfolio, CASH, PORTFOLIO
from returns_metrics import ReturnsMetrics
from settings import T_SCORE, MAX_TRADE


class Optimizer:
    """Принимает портфель и выбирает наиболее оптимальное направление его улучшения

    При выборе направления улучшения выбираются только те, которые обеспечивают улучшение по каждому из критериев:
    нижней границе дивидендов и величине просадки. На преимущества акций с маленьким оборотом накладывается понижающий
    коэффициент

    Дополнительно производится оценка возможности значимо увеличить (на T_SCORE СКО) -  используется не точный расчет, а
    линейное приближение. Производится выбор, где можно достичь большего увеличения - по величине просадки или
    минимальным дивидендам
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

        if self.t_dividends_growth > self.t_drawdown_growth:
            t_growth = self.t_dividends_growth
            best_gradient = 'дивидендов'
            best_growth = self.dividends_gradient_growth
        else:
            t_growth = self.t_drawdown_growth
            best_gradient = 'просадки'
            best_growth = self.drawdown_gradient_growth
        if t_growth > T_SCORE:
            need_optimization = (f'ОПТИМИЗАЦИЯ ТРЕБУЕТСЯ'
                                 f'\nПрирост {best_gradient} составляет {t_growth:.2f} СКО > {T_SCORE:.2f}')
        else:
            need_optimization = (f'ОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ'
                                 f'\nПрирост {best_gradient} составляет {t_growth:.2f} СКО < {T_SCORE:.2f}')

        frames = [self.dividends_metrics.gradient,
                  self.returns_metrics.gradient,
                  self.dominated,
                  self.portfolio.volume_factor,
                  best_growth]
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

    def _dividends_growth_matrix(self):
        """Матрица увеличения градиента дивидендов при замене бумаги в строке на бумагу в столбце

        Бумаги с нулевым весом не могут быть проданы, поэтому прирост градиента 0
        Продажи не ведущие к увеличению градиента доходности так же не рассматриваются
        """
        dividends_gradient = self.dividends_metrics.gradient
        volume_factor = self.portfolio.volume_factor
        dividends_growth = dividends_gradient.apply(func=lambda x: (dividends_gradient - x) * volume_factor)
        dividends_growth.loc[self.portfolio.weight == 0] = 0
        returns_gradient = self.returns_metrics.gradient
        dividends_growth = dividends_growth * returns_gradient.apply(func=lambda x: returns_gradient > x)
        dividends_growth[dividends_growth <= 0] = 0
        return dividends_growth

    def _drawdown_growth_matrix(self):
        """Матрица увеличения градиента просадки при замене бумаги в строке на бумагу в столбце

        Бумаги с нулевым весом не могут быть проданы, поэтому прирост градиента 0
        Продажи не ведущие к увеличению градиента доходности так же не рассматриваются
        """
        drawdown_gradient = self.returns_metrics.gradient
        volume_factor = self.portfolio.volume_factor
        drawdown_growth = drawdown_gradient.apply(func=lambda x: (drawdown_gradient - x) * volume_factor)
        drawdown_growth.loc[self.portfolio.weight == 0] = 0
        dividends_gradient = self.dividends_metrics.gradient
        drawdown_growth = drawdown_growth * dividends_gradient.apply(func=lambda x: dividends_gradient > x)
        drawdown_growth[drawdown_growth <= 0] = 0
        return drawdown_growth

    @property
    def dividends_gradient_growth(self):
        """Для каждой позиции выдает прирост градиента дивидендов при покупке доминирующей

        Для позиций не имеющих доминирующих - прирост 0
        Учитывается понижающий коэффициент для низколиквидных доминирующих акций
        """
        matrix = self._dividends_growth_matrix()
        return matrix.apply(func=lambda x: x.max(), axis='columns')

    @property
    def drawdown_gradient_growth(self):
        """Для каждой позиции выдает прирост градиента просадки при покупке доминирующей

        Для позиций не имеющих доминирующих - прирост 0
        Учитывается понижающий коэффициент для низколиквидных доминирующих акций
        """
        matrix = self._drawdown_growth_matrix()
        return matrix.apply(func=lambda x: x.max(), axis='columns')

    @property
    def t_dividends_growth(self):
        """Приблизительная оценка потенциального улучшения минимальных дивидендов

        Линейное приближение - доля позиций умножается на градиент роста. Результат нормируется на СКО
        дивидендов портфеля для удобства сравнения с критическим уровнем t-статистик
        """
        weighted_growth = (self.portfolio.weight * self.dividends_gradient_growth).sum()
        return weighted_growth / self.dividends_metrics.std[PORTFOLIO]

    @property
    def t_drawdown_growth(self):
        """Приблизительная оценка потенциального улучшения просадки

        Линейное приближение - доля позиций умножается на градиент роста. Результат нормируется на СКО
        дивидендов портфеля для удобства сравнения с критическим уровнем t-статистик
        """
        weighted_growth = (self.portfolio.weight * self.drawdown_gradient_growth).sum()
        return weighted_growth / self.returns_metrics.std[PORTFOLIO]

    @property
    def dominated(self):
        """Для каждой позиции выдает доминирующую ее по Парето

        Если доминирующих несколько, то выбирается позиция с максимальным ростом градиента
        Предпочтение отдается приросту градиента с большим потенциалом увеличения t-статистики
        Учитывается понижающий коэффициент для низколиквидных доминирующих акций
        """
        if self.t_dividends_growth > self.t_drawdown_growth:
            matrix = self._dividends_growth_matrix()
        else:
            matrix = self._drawdown_growth_matrix()
        return matrix.apply(func=lambda x: x.idxmax() if x.max() > 0 else "",
                            axis='columns')

    @property
    def best_trade(self):
        """Возвращает строчку с рекомендацией по сделкам

        Предпочтение отдается приросту градиента с большим потенциалом увеличения t-статистики и позиции с максимальным
        приростом градиента

        Лучшая позиция на продажу сокращается до нуля, но не более чем на MAX_TRADE от объема портфеля
        Продажа бьется на 5 сделок с округлением в большую сторону

        Лучшая покупка осуществляется на объем доступного кэша, но не более чем на MAX_TRADE от объема портфеля
        Покупка бьется на 5 сделок
        """
        portfolio = self.portfolio
        # Отбрасывается портфель и кэш из рекомендаций
        if self.t_dividends_growth > self.t_drawdown_growth:
            best_sell = self.dividends_gradient_growth.iloc[:-2].idxmax()
        else:
            best_sell = self.drawdown_gradient_growth.iloc[:-2].idxmax()
        sell_weight = max(0, min(portfolio.weight[best_sell], MAX_TRADE - portfolio.weight[CASH]))
        sell_value = sell_weight * portfolio.value[PORTFOLIO]
        sell_5_lots = int(round(sell_value / portfolio.lot_size[best_sell] / portfolio.price[best_sell] / 5 + 0.5))
        best_buy = self.dominated[best_sell]
        buy_value = min(portfolio.value[CASH], MAX_TRADE * portfolio.value[PORTFOLIO])
        buy_5_lots = int(buy_value / portfolio.lot_size[best_buy] / portfolio.price[best_buy] / 5)
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
               LKOH=123)
    port = Portfolio(date='2018-04-06',
                     cash=4330.3,
                     positions=pos)
    optimizer = Optimizer(port)
    print(optimizer)
