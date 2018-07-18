"""Пример использования на основе реалистичного портфеля и тест скорости исполнения"""

import cProfile
import pstats

from optimizer import Optimizer
from portfolio import Portfolio

POSITIONS = dict(BANEP=200,
                 MFON=55,
                 SNGSP=235,
                 MSTT=4435,
                 KBTK=9,
                 RTKMP=1504,
                 LSRG=561,
                 LSNGP=81,
                 PRTK=70,
                 MTSS=749,
                 AKRN=795,
                 MRKC=36,
                 MSRS=699,
                 UPRO=1267,
                 PMSBP=1683,
                 GMKN=166,
                 VSMO=73,
                 RSTIP=87,
                 LKOH=123,
                 ENRU=319,
                 MVID=264)
CASH = 308_463
DATE = '2018-04-20'


def trading():
    """Распечатка всей аналитики, необходимой для управления портфелем"""
    port = Portfolio(date=DATE,
                     cash=CASH,
                     positions=POSITIONS)
    optimizer = Optimizer(port)
    print(optimizer.portfolio)
    print(optimizer.dividends_metrics)
    print(optimizer.returns_metrics)
    print(optimizer)


def speed_test():
    """Функция тестирования скорости

    Используется реалистичный портфель и комплексные функции распечатки метрик портфеля
    """
    pr = cProfile.Profile()
    pr.enable()

    trading()

    pr.disable()
    ps = pstats.Stats(pr).sort_stats('cumulative')
    ps.print_stats()


if __name__ == '__main__':
    speed_test()
