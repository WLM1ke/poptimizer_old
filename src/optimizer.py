"""Класс проводит оптимизацию по Парето на основе метрик доходности и дивидендов"""

import pandas as pd

from dividends_metrics_classic import ClassicDividendsMetrics
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
        self._dividends_metrics = ClassicDividendsMetrics(portfolio)
        self._returns_metrics = ReturnsMetrics(portfolio)

    def __str__(self):
        return (f'\n{self._str_main_metrics()}'
                f'\n'
                f'\n{self._str_need_optimization()}'
                f'\n'
                f'\n{self._str_best_trade()}'
                f'\n'
                f'\nКЛЮЧЕВЫЕ МЕТРИКИ ОПТИМАЛЬНОСТИ ПО ПАРЕТО'
                f'\n'
                f'\n{self._str_pareto_metrics()}')

    def _str_main_metrics(self):
        """Срока с информацией о просадке и дивидендах портфеля"""
        draw_down = self._returns_metrics.draw_down[PORTFOLIO]
        expected_dividends = self._dividends_metrics.expected_dividends
        minimal_dividends = self._dividends_metrics.minimal_dividends
        return (f'КЛЮЧЕВЫЕ МЕТРИКИ ПОРТФЕЛЯ'
                f'\nМаксимальная ожидаемая просадка - {draw_down:.4f}'
                f'\nОжидаемые дивиденды - {expected_dividends:.0f}'
                f'\nМинимальные дивиденды - {minimal_dividends:.0f}')

    def _str_need_optimization(self):
        """Строка о необходимости оптимизации"""
        t_dividends = self.t_dividends_growth
        t_drawdown = self.t_drawdown_growth
        if max(t_dividends, t_drawdown) > T_SCORE:
            str_beginning = f'ОПТИМИЗАЦИЯ ТРЕБУЕТСЯ'
        else:
            str_beginning = f'ОПТИМИЗАЦИЯ НЕ ТРЕБУЕТСЯ'
        return (f'{str_beginning}'
                f'\nПрирост дивидендов - {t_dividends:.2f} СКО'
                f'\nПрирост просадки - {t_drawdown:.2f} СКО')

    def _str_best_trade(self):
        """Возвращает строчку с рекомендацией по сделкам

        Предпочтение отдается перемене позиций максимально увеличивающих дивиденды

        Лучшая позиция на продажу сокращается до нуля, но не более чем на MAX_TRADE от объема портфеля
        Продажа бьется на 5 сделок минимум по 1 лоту

        Лучшая покупка осуществляется на объем доступного кэша, но не более чем на MAX_TRADE от объема портфеля
        Покупка бьется на 5 сделок минимум по 1 лоту
        """
        portfolio = self.portfolio
        # Отбрасывается портфель и кэш из рекомендаций
        best_sell = self.dividends_gradient_growth.iloc[:-2].idxmax()
        sell_weight = max(0, min(portfolio.weight[best_sell], MAX_TRADE - portfolio.weight[CASH]))
        sell_value = sell_weight * portfolio.value[PORTFOLIO]
        sell_5_lots = max(1, int(sell_value / portfolio.lot_size[best_sell] / portfolio.price[best_sell] / 5 + 0.5))
        best_buy = self.dominated[best_sell]
        buy_value = min(portfolio.value[CASH], MAX_TRADE * portfolio.value[PORTFOLIO])
        buy_5_lots = max(1, int(buy_value / portfolio.lot_size[best_buy] / portfolio.price[best_buy] / 5))
        return (f'РЕКОМЕНДУЕТСЯ'
                f'\nПродать {best_sell} - 5 сделок по {sell_5_lots} лотов'
                f'\nКупить {best_buy} - 5 сделок по {buy_5_lots} лотов')

    def _str_pareto_metrics(self):
        """Сводная информация об оптимальности по Парето"""
        frames = [self.dividends_metrics.gradient,
                  self.returns_metrics.gradient,
                  self.dominated,
                  self.portfolio.volume_factor,
                  self.dividends_gradient_growth,
                  self.drawdown_gradient_growth]
        pareto_metrics = pd.concat(frames, axis=1)
        pareto_metrics.columns = ['D_GRADIENT', 'R_GRADIENT', 'DOMINATED', 'VOLUME_FACTOR', 'DIVIDENDS_GROWTH',
                                  'DRAWDOWN_GROWTH']
        pareto_metrics.sort_values('D_GRADIENT', ascending=False, inplace=True)
        return pareto_metrics

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
        Портфель и кэш не могут доминировать
        """
        matrix = self._dividends_growth_matrix().iloc[:, :-2]
        return matrix.apply(func=lambda x: x.max(), axis='columns')

    @property
    def drawdown_gradient_growth(self):
        """Для каждой позиции выдает прирост градиента просадки при покупке доминирующей

        Для позиций не имеющих доминирующих - прирост 0
        Учитывается понижающий коэффициент для низколиквидных доминирующих акций
        Портфель и кэш не могут доминировать
        """
        matrix = self._drawdown_growth_matrix().iloc[:, :-2]
        return matrix.apply(func=lambda x: x.max(), axis='columns')

    @property
    def t_dividends_growth(self):
        """Приблизительная оценка потенциального улучшения минимальных дивидендов

        Линейное приближение - доля позиций умножается на градиент роста. Результат нормируется на СКО
        дивидендов портфеля для удобства сравнения с критическим уровнем t-статистик
        Портфель и кэш исключаются из расчетов
        """
        weighted_growth = (self.portfolio.weight * self.dividends_gradient_growth)[:-2].sum()
        return weighted_growth / self.dividends_metrics.std[PORTFOLIO]

    @property
    def t_drawdown_growth(self):
        """Приблизительная оценка потенциального улучшения просадки

        Линейное приближение - доля позиций умножается на градиент роста. Результат нормируется на СКО
        дивидендов портфеля для удобства сравнения с критическим уровнем t-статистик
        Портфель и кэш исключаются из расчетов
        """
        weighted_growth = (self.portfolio.weight * self.drawdown_gradient_growth)[:-2].sum()
        return weighted_growth / self.returns_metrics.std_at_draw_down

    @property
    def dominated(self):
        """Для каждой позиции выдает доминирующую ее по Парето

        Если доминирующих несколько, то выбирается позиция с максимальным ростом градиента дивидендов
        Портфель и кэш не доминируются
        """
        matrix = self._dividends_growth_matrix().iloc[:, :-2]
        df = matrix.apply(func=lambda x: x.idxmax() if x.max() > 0 else "",
                          axis='columns')
        df[-2:] = ""
        return df


if __name__ == '__main__':
    POSITIONS = dict(AKRN=679,
                     BANEP=392,
                     CHMF=173,
                     GMKN=139,
                     LKOH=123,
                     LSNGP=59,
                     LSRG=1341,
                     MSRS=38,
                     MSTT=2181,
                     MTSS=1264,
                     MVID=141,
                     PMSBP=2715,
                     RTKMP=1674,
                     SNGSP=263,
                     TTLK=234,
                     UPRO=1272,
                     VSMO=101)
    port = Portfolio(date='2018-07-24',
                     cash=102_262,
                     positions=POSITIONS)
    optimizer = Optimizer(port)
    print(optimizer)
    dfs = [optimizer.dividends_metrics.gradient,
           optimizer.returns_metrics.gradient,
           optimizer.portfolio.weight,
           optimizer.portfolio.volume_factor]
    print(optimizer.dividends_metrics.std[PORTFOLIO])
    print(optimizer.returns_metrics.std_at_draw_down)
    # pd.concat(dfs, axis='columns').to_excel('data.xlsx')
